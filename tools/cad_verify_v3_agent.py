"""Explicit VERIFY v3 driver. No changes to the MVP/v1 generation loops."""
import ast
import codecs
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

if __package__:
    from . import cad_agent as agent, cad_spec, cad_verify_v3_probe as probe, eval_verify
    from .cad_verify_guard import clarification, CLARIFICATION_FIELDS, QUESTIONS, q_score
    from .cad_verify_v3_guard import Budget, Stop
else:
    import cad_agent as agent, cad_spec, cad_verify_v3_probe as probe, eval_verify
    from cad_verify_guard import clarification, CLARIFICATION_FIELDS, QUESTIONS, q_score
    from cad_verify_v3_guard import Budget, Stop


CAPABILITY_ALLOWLIST=frozenset(('unsupported_shaft_operation',))
PROVIDER_ALLOWLIST=frozenset(('server_overloaded',))
PROVIDER_POLICY='solfix-600s-unlimited-v1'
PROVIDER_WAIT_S=600
CAPTURE_BYTES=16384
EVENT_CHARS=1048576


class StreamCapture:
    """Hash every byte, retain a bounded UTF-8 tail, and inspect events as they arrive."""
    def __init__(self,parse=False):
        self.parse=parse;self.hash=hashlib.sha256();self.full_bytes=0;self.tail=b''
        self.line='';self.skipping=False;self.complete=True;self.output=False
        self.codes=[];self.shapes=[];self.session=None;self.usage=[];self.event_index=0

    def event(self,line):
        index=self.event_index;self.event_index+=1
        try:event=agent.loads(line)
        except ValueError:return
        if not isinstance(event,dict):return
        kind=event.get('type');payload=event.get('payload') if kind in ('event_msg','response_item') else event
        if kind=='thread.started':self.session=agent.clean(event.get('thread_id'))
        if kind=='turn.completed' and isinstance(event.get('usage'),dict):
            if len(self.usage)<64:self.usage.append(dict(event_index=index,values=agent.clean({k:event['usage'].get(k) for k in agent.USAGE_KEYS})))
            else:self.complete=False
        if not isinstance(payload,dict):return
        pkind=payload.get('type')
        error=payload.get('error') if pkind in ('error','turn.failed','task_complete') else None
        info=error.get('codex_error_info') if isinstance(error,dict) else payload.get('codex_error_info') if pkind=='error' else None
        if isinstance(info,str):
            if info not in self.codes:
                if len(self.codes)<32:self.codes.append(info)
                else:self.complete=False
            shape=[kind,pkind]
            if shape not in self.shapes and len(self.shapes)<32:self.shapes.append(shape)
        item=payload.get('item') if pkind in ('item.started','item.updated','item.completed') else payload
        if isinstance(item,dict):
            if item.get('type') in ('agent_message','agent_message_delta') and (item.get('text') or item.get('message') or item.get('delta')):self.output=True
            if item.get('type')=='message' and item.get('role')=='assistant' and item.get('content'):self.output=True
        if pkind=='task_complete' and payload.get('last_agent_message'):self.output=True

    def feed(self,text):
        raw=text.encode('utf-8');self.hash.update(raw);self.full_bytes+=len(raw)
        self.tail=(self.tail+raw)[-CAPTURE_BYTES:]
        if not self.parse:return
        parts=text.split('\n')
        for i,part in enumerate(parts):
            if not self.skipping:
                if len(self.line)+len(part)>EVENT_CHARS:self.line='';self.skipping=True;self.complete=False
                else:self.line+=part
            if i<len(parts)-1:
                if not self.skipping:self.event(self.line)
                self.line='';self.skipping=False

    def finish(self):
        if self.parse and self.line and not self.skipping:self.event(self.line)
        self.line=''

    def summary(self,final=None,source='stdout'):
        output=self.output or bool(final)
        return dict(error_infos=self.codes,assistant_output=output,event_shapes=self.shapes,source=source,
            full_sha256=self.hash.hexdigest(),parse_complete=self.complete,
            provider_rejected=bool(self.complete and self.codes and set(self.codes)<=PROVIDER_ALLOWLIST and not output))

    def artifact(self):
        tail=self.tail.decode('utf-8',errors='ignore').encode('utf-8')
        return dict(tail=tail,full_sha256=self.hash.hexdigest(),full_bytes=self.full_bytes)


def provider_summary(stdout,final=None,source='stdout'):
    capture=StreamCapture(parse=True)
    for start in range(0,len(stdout),8192):capture.feed(stdout[start:start+8192])
    capture.finish();return capture.summary(final,source)


def bounded_run(argv,**kwargs):
    """Production exec transport never buffers complete stdout/stderr in memory."""
    if len(argv)<2 or argv[1]!='exec':return subprocess.run(argv,**kwargs)
    options=dict(kwargs);timeout=options.pop('timeout',None)
    for key in ('capture_output','text','encoding','errors'):options.pop(key,None)
    captures={k:StreamCapture(parse=k=='stdout') for k in ('stdout','stderr')};errors=[]
    def drain(pipe,capture):
        decoder=codecs.getincrementaldecoder('utf-8')(errors='replace')
        try:
            with pipe:
                while True:
                    chunk=pipe.read(8192)
                    if not chunk:break
                    capture.feed(decoder.decode(chunk))
                capture.feed(decoder.decode(b'',final=True));capture.finish()
        except OSError as exc:errors.append(exc)
    with subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,**options) as process:
        threads=[threading.Thread(target=drain,args=(getattr(process,k),v),daemon=True) for k,v in captures.items()]
        for thread in threads:thread.start()
        failure=None
        try:process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            failure=exc;process.kill();process.wait()
        finally:
            for thread in threads:thread.join()
        stdout,stderr=(captures[k].tail.decode('utf-8',errors='ignore') for k in ('stdout','stderr'))
        completed=subprocess.CompletedProcess(argv,process.returncode,stdout,stderr)
        completed.transport_capture={k:v.artifact() for k,v in captures.items()}
        completed.provider_summary=captures['stdout'].summary()
        completed.exec_metadata=(captures['stdout'].session,captures['stdout'].usage or None)
        if failure:
            failure.output=stdout;failure.stderr=stderr
            failure.transport_capture=completed.transport_capture;failure.exec_metadata=completed.exec_metadata
            failure.provider_summary=completed.provider_summary
            raise failure
        if errors:raise errors[0]
        return completed


def rollout_summary(session_id,final=None,home=None):
    """CLI versions may omit the typed error in stdout. Bind its actual session event.

    Read only the uniquely named session; retain hashes/typed metadata, never its
    prompt/config/credentials or full contents. No free-text fallback.
    """
    if not isinstance(session_id,str) or not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',session_id):return None
    account=Path(home or os.environ.get('CODEX_HOME') or Path.home()/'.codex')
    matches=list((account/'sessions').glob('*/*/*/*'+session_id+'*.jsonl'))
    if len(matches)!=1:return None
    capture=StreamCapture(parse=True)
    try:
        with matches[0].open(encoding='utf-8') as file:
            while True:
                chunk=file.read(8192)
                if not chunk:break
                capture.feed(chunk)
    except (OSError,UnicodeError):return None
    capture.finish();summary=capture.summary(final,'rollout')
    summary['session_id']=session_id
    return summary


def capture_transport(out,root,row,completed,summary):
    row['provider_summary']=summary;row['transport_artifacts']={}
    for key,value in (('stdout',completed.stdout or ''),('stderr',completed.stderr or '')):
        captured=getattr(completed,'transport_capture',None)
        if captured:item=captured[key];tail=item['tail'];full_sha=item['full_sha256'];full_bytes=item['full_bytes']
        else:
            raw=value.encode('utf-8');tail=raw[-CAPTURE_BYTES:].decode('utf-8',errors='ignore').encode('utf-8');full_sha=hashlib.sha256(raw).hexdigest();full_bytes=len(raw)
        p=out/('call-c%d-%s-tail.txt'%(row['call'],key))
        with p.open('xb') as file:file.write(tail)
        row['transport_artifacts'][key]=dict(path=p.relative_to(root).as_posix(),sha256=hashlib.sha256(tail).hexdigest(),
            full_sha256=full_sha,full_bytes=full_bytes,bytes=len(tail))
    p=out/('call-c%d-provider.json'%row['call'])
    with p.open('x',encoding='utf-8') as file:json.dump(summary,file,allow_nan=False)
    row['provider_artifact']=dict(path=p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def wait_provider(row,budget,guard,logical_deadline,sleeper=None):
    """Backoff is wall time, never a new clock or a provider failure/stop."""
    row.update(wait_requested_s=PROVIDER_WAIT_S,backoff_s=0)
    sleep=sleeper or time.sleep
    while row['backoff_s']<PROVIDER_WAIT_S:
        available=min(logical_deadline-budget.clock(),budget.remaining(),guard.remaining() if guard else 900)
        if available<=0:raise Stop('episode_stage_deadline_exceeded')
        delay=min(60,PROVIDER_WAIT_S-row['backoff_s'],available)
        sleep(delay);row['backoff_s']+=delay
        if delay==available and row['backoff_s']<PROVIDER_WAIT_S:
            if guard:guard.remaining()
            raise Stop('episode_stage_deadline_exceeded')
CAPABILITY_CONTRACT=(
    'The compiler supports exactly rect_prism, rect_stack, stepped_shaft. '
    'Rectangular families support axis-aligned connected stock regions, rectangular top pockets, '
    'Z through holes and top_outer fillet/chamfer within the build schema and compiler limits. '
    'stepped_shaft supports coaxial solid steps only, without bore, holes, pockets or finish. '
    'Tapers, curved pipes, ribs, circular flanges, hollow/grooved rollers and other unrepresentable '
    'features must return a well-formed unsupported list. Do not invent new families or fields.')
REPAIR_CONTRACT=(
    'Keep user-stated dimensions editable on the geometry that they control. '
    'A radial groove depth can be a constrained radial span between the actual stock and bottom '
    'boundaries, a difference of their driven radii, or half a difference of their driven diameters. '
    'Groove width can be an operative length or driven axial boundary difference; half-width '
    'requires active symmetry proving both boundaries and their driven center. '
    'Use native constraints/features, not detached numbers or inactive properties. '
    'No unstated derived dimension is independently required.')


def interpretation(raw, source_enabled=False):
    """Schema first, and only the exact signed compiler capability is bypassed."""
    if isinstance(raw,dict) and set(raw)=={'unsupported'}:
        if not isinstance(raw['unsupported'],list) or not raw['unsupported'] or any(not isinstance(x,str) or not x for x in raw['unsupported']):
            raise ValueError('unsupported_contract')
        return 'unsupported',raw,dict(raw=raw,schema_valid=None,compiler_supported=None,capability_code=None,unsupported_origin='model')
    if isinstance(raw,dict) and set(raw)=={'needs_clarification'}:
        clarification(raw)
        return 'needs_clarification',raw,dict(raw=raw,schema_valid=None,compiler_supported=None,capability_code=None,unsupported_origin=None)
    schema=cad_spec.read_json(cad_spec.SCHEMA_PATH.read_text(encoding='utf-8'))
    cad_spec.schema_check(raw,schema,schema)
    try:spec=cad_spec.validate_spec(raw)
    except ValueError as exc:
        if not source_enabled or str(exc) not in CAPABILITY_ALLOWLIST:raise
        return 'unsupported',raw,dict(raw=raw,schema_valid=True,compiler_supported=False,capability_code=str(exc),unsupported_origin='validator')
    return 'spec',spec,dict(raw=raw,schema_valid=True,compiler_supported=True,capability_code=None,unsupported_origin=None)


def feedback(target, candidate, result):
    """Keep live failed checks; large reachability proof stays in the CAD report."""
    measured = json.loads(json.dumps(result.get("measurements")))
    details = result.get("predicate_details") or {}
    observed = {key: result.get(key) for key in agent.FEEDBACK_KEYS if key not in ("measurements", "predicate_details")}
    observed.update(measurements=measured, predicate_details={key: value for key, value in details.items() if key != "checks"})
    observed["predicate_details"]["checks"] = [row for row in details.get("checks", []) if row.get("passed") is False]
    return {"source" if target == "source" else "build_spec": candidate, "result": observed}


def run_driver(name, codex, input_text, gold_path, *, root=agent.ROOT, runner=None, clock=None,
               route="spec", max_calls=None, rubric=None, answer=None, fault=None, guard=None, preview=False,
               provider_retry=False,sleeper=None,prior_provider_attempts=0,prior_call_identity=None):
    if route not in ("source", "spec", "ask", "completion") or not (name.endswith('-mvp1') or provider_retry and name.endswith('-mvp1-resume1')):
        raise ValueError("verify_v3_options")
    if route == "completion" and (not isinstance(answer, str) or not rubric or preview):
        raise ValueError("verify_v3_answer_contract")
    if route == "ask" and not rubric:
        raise ValueError("verify_v3_rubric_required")
    cap = 4 if route in ("source", "completion") else 1 if route == "ask" else 3
    max_calls = cap if max_calls is None else max_calls
    if not 1 <= max_calls <= cap:
        raise ValueError("verify_v3_call_contract")
    if type(prior_provider_attempts) is not int or prior_provider_attempts<0 or prior_provider_attempts and not provider_retry:
        raise ValueError('provider_retry_seed')
    root = Path(root).resolve()
    budget = Budget(max_calls, clock or (guard.clock if guard else None), preview)
    if guard: guard.before_episode(max_calls)
    gold_path = Path(gold_path).resolve() if gold_path else None
    gold = probe.load_gold(gold_path) if gold_path else None
    completion_text = input_text+"\n"+answer if answer is not None else None
    if route != "ask":
        if gold is None or gold["description"] != (completion_text if route == "completion" else input_text):
            raise ValueError("description_gold_identity")
        if not preview and (gold["provenance"]["authority"] != "human" or gold["provenance"]["confirmed"] is not True):
            raise ValueError("eval_human_gold_required")
    if rubric and rubric.get("description_sha256") != agent.digest(input_text):
        raise ValueError("rubric_description_binding")
    runner = runner or (bounded_run if provider_retry else subprocess.run)
    out = agent.new_run_dir(root, name)
    report = dict(schema="cad-harness.cad_agent.verify3", run_id=name, mode="description", probe_profile="verify-v3",
        task_id=gold["case_id"] if gold else rubric["case_id"], description_sha256=agent.digest(input_text),
        input_sha256=agent.digest(input_text), gold_sha256=hashlib.sha256(gold_path.read_bytes()).hexdigest() if gold else None,
        started_at=agent.utc(), status="failed", message_code=None, calls=[], attempts=[], first_response=None,
        unsupported_to_source=False, final_out_dir=None, geometry_ok=None, route=route, preview=preview,
        repair_eligible=False, repair_not_attempted_reason=None, fault=fault.record if fault else None,
        interpretations=[], unsupported_origin=None)
    if provider_retry:report.update(provider_policy=PROVIDER_POLICY,prior_provider_attempts=prior_provider_attempts)
    if answer is not None:
        report.update(answer_sha256=agent.digest(answer), completion_input_sha256=agent.digest(completion_text),
                      completion_reached=False, initial_q_score=None, initial_critical_invention=False)
    target, previous, candidate, last_spec = "spec", None, None, None
    prompt = input_text

    def consume_response(purpose,row):
        # Eligibility was checked before invocation. A late response is still a
        # real observation, even if the stage clock expired during transport.
        budget.counts[purpose]+=1;budget.calls+=1;row['slot_consumed']=True

    def invoke(purpose):
        nonlocal prompt, previous
        budget.check_call(purpose)
        timeout = budget.sol_timeout(purpose)
        if guard:timeout=min(timeout,guard.remaining())
        contract = agent.spec_contract(schema_text) if target == "spec" else (
            "Return only complete Python source defining build(doc) and returning its Body. "
            "Allowed imports: FreeCAD, Part, Sketcher, math. No file, shell, network, document lifecycle, save or probe operations.")
        if target == "spec":
            contract += '\n'+CAPABILITY_CONTRACT
            contract += ("\nVERIFY clarification contract: needs_clarification is a list of necessary missing field IDs only, "
                "never natural-language questions or invented values. Allowed field IDs: "+", ".join(CLARIFICATION_FIELDS)+".")
        if budget.stage == "repair": contract += "\nRetain this output path for CAD repair; no unsupported or clarification fallback.\n"+REPAIR_CONTRACT
        context = agent.developer_context(skill, contract, previous)
        if provider_retry and budget.calls==0 and prior_call_identity is not None:
            identity=dict(kind=target,purpose=purpose,context_sha256=agent.digest(context),prompt_sha256=agent.digest(prompt))
            if any(identity[k]!=prior_call_identity.get(k) for k in identity):raise Stop('resume_A5_payload_binding')
        parent = Path(tempfile.gettempdir()).resolve()
        if parent.is_relative_to(root): raise ValueError("exec_temp_inside_repository")
        logical=budget.calls+1
        logical_deadline=budget.clock()+timeout
        seed=prior_provider_attempts if logical==1 else 0
        with tempfile.TemporaryDirectory(prefix="cad-verify-v3-", dir=parent) as directory:
            work = Path(directory); last = work/"last.txt"
            argv = agent.exec_argv(codex, work, last, prompt, context)
            transport=seed
            while True:
                transport+=1
                timeout=min(budget.sol_timeout(purpose),logical_deadline-budget.clock())
                if guard:timeout=min(timeout,guard.remaining())
                if timeout<=0:raise Stop('episode_stage_deadline_exceeded')
                tick=budget.clock()
                row = dict(call=len(report['calls'])+1,kind=target,purpose=purpose,stage=budget.stage,
                    context_sha256=agent.digest(context),prompt_sha256=agent.digest(prompt),started_at=agent.utc(),usage=None,
                    timeout_s=timeout,elapsed_s=tick-budget.started)
                if provider_retry:row.update(logical_call=logical,transport_attempt=transport,
                    argv_sha256=agent.digest(json.dumps(argv,ensure_ascii=False)),slot_consumed=False,provider_rejected=False)
                snapshot = guard.before_call() if guard else None
                if not provider_retry:budget.call(purpose)
                if guard: row["quota_snapshot"] = snapshot
                row["invoked"] = True
                if provider_retry or target=='source' or budget.stage=='repair':
                    row['context_artifacts']={}
                    for key,value in (('prompt',prompt),('context',context)):
                        path=out/('call-c%d-%s.txt'%(row['call'],key))
                        with path.open('xb') as artifact:artifact.write(value.encode('utf-8'))
                        row['context_artifacts'][key]=dict(path=path.relative_to(root).as_posix(),sha256=agent.digest(value))
                report["calls"].append(row)
                if route == "completion" and purpose == "interpretation":
                    report["completion_reached"] = True
                try:
                    completed = runner(argv,cwd=str(work),capture_output=True,text=True,encoding='utf-8',errors='replace',shell=False,
                        stdin=subprocess.DEVNULL,timeout=timeout)
                    row['exit']=completed.returncode
                    row['session_id'],row['usage']=getattr(completed,'exec_metadata',None) or agent.exec_metadata(completed.stdout)
                    final=last.read_text(encoding='utf-8-sig') if last.is_file() else None
                    if provider_retry:
                        summary=dict(completed.provider_summary) if hasattr(completed,'provider_summary') else provider_summary(completed.stdout,final)
                        if final:summary.update(assistant_output=True,provider_rejected=False)
                        if not summary['error_infos'] and (completed.returncode!=0 or not final):
                            fallback=rollout_summary(row['session_id'],final)
                            if fallback:
                                fallback['assistant_output'] |= summary['assistant_output']
                                fallback['provider_rejected'] &= not summary['assistant_output'] and summary.get('parse_complete',True)
                                summary=fallback
                        capture_transport(out,root,row,completed,summary)
                        row['provider_rejected']=summary['provider_rejected']
                        if row['provider_rejected'] and guard:guard.calls-=1
                        if not row['provider_rejected']:consume_response(purpose,row)
                    if not provider_retry or not row['provider_rejected']:
                        if completed.returncode!=0 or final is None:raise ValueError('exec_nonzero_or_missing_final')
                        if str(work).lower() in final.lower() or work.as_posix().lower() in final.lower():raise ValueError('private_source')
                        (out/('last-c%d.txt'%row['call'])).write_bytes(agent.clean(final).encode('utf-8'))
                        if logical==1:report['first_response_call']=row['call']
                        return final
                except (OSError,subprocess.SubprocessError) as exc:
                    if provider_retry and 'transport_artifacts' not in row:
                        text=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v or ''
                        failed=subprocess.CompletedProcess(argv,None,text(getattr(exc,'stdout',None)),text(getattr(exc,'stderr',None)))
                        if hasattr(exc,'transport_capture'):failed.transport_capture=exc.transport_capture
                        summary=dict(exc.provider_summary) if hasattr(exc,'provider_summary') else provider_summary(failed.stdout)
                        summary.update(provider_rejected=False,transport_error=type(exc).__name__)
                        row['session_id'],row['usage']=getattr(exc,'exec_metadata',None) or agent.exec_metadata(failed.stdout)
                        capture_transport(out,root,row,failed,summary);row['error_type']=type(exc).__name__
                        consume_response(purpose,row)
                    raise
                finally:row.update(ended_at=agent.utc(),wall_ms=(budget.clock()-tick)*1000)
                wait_provider(row,budget,guard,logical_deadline,sleeper)

    def parse(final):
        if target == "source":
            value = agent.source_from_final(final)
            agent.cad_run.source_contract(ast.parse(value))
            return "source", value, None
        raw = cad_spec.read_json(agent.strip_final_fence(final, "json", "spec"))
        kind,value,decision=interpretation(raw,source_enabled=route=='source' and budget.stage=='initial' and budget.attempts==0)
        report['interpretations'].append(dict(call=report['calls'][-1]['call'],**decision))
        if kind=='unsupported':report['unsupported_origin']=decision['unsupported_origin']
        return kind,value,raw

    try:
        skill = (root/"skills/freecad-modeling/SKILL.md").read_text(encoding="utf-8")
        schema_text = (root/"design/cad-harness-mvp/build-schema.json").read_text(encoding="utf-8")
        report.update(skill_sha256=agent.digest(skill), schema_sha256=agent.digest(schema_text),
            compiler_sha256=hashlib.sha256(Path(cad_spec.__file__).read_bytes()).hexdigest(),
            probe_sha256=hashlib.sha256(Path(probe.__file__).read_bytes()).hexdigest(),
            shared_probe_sha256=hashlib.sha256(Path(probe.v1.__file__).read_bytes()).hexdigest(),
            agents_sha256=agent.agents_identity(root), settings={**budget.settings(), "model": agent.MODEL,
                "effort": agent.EFFORT, "disabled": list(agent.DISABLED), "sandbox": "read-only", "skip_git_repo_check": True})
        if route == "ask":
            report["settings"].update(max_cad_attempts=0, parse_calls=0, repair_calls=0)
        version = runner([codex, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                         shell=False, stdin=subprocess.DEVNULL, timeout=budget.remaining())
        if version.returncode != 0: raise ValueError("cli_version_failed")
        report["cli_version"] = agent.clean(version.stdout.strip())
        purpose = "question" if route in ("ask", "completion") else "interpretation"
        while True:
            final = invoke(purpose)
            budget.remaining()
            initial = budget.calls == 1
            if initial: report["first_response"] = dict(kind="invalid", sha256=agent.digest(final))
            try:
                kind, candidate, raw = parse(final)
                if initial:
                    first = report["first_response"]
                    first.update(kind=kind, raw=raw)
                    if kind == "spec":
                        bounds = candidate.get("regions", [{}])[0].get("bounds", []) if candidate.get("regions") else []
                        first["binding_defaults_ok"] = len(bounds) == 6 and abs(bounds[0]+bounds[1]) < 1e-9 and abs(bounds[2]+bounds[3]) < 1e-9 and bounds[4] == 0
                    if kind == "needs_clarification": first["fields"] = clarification(candidate)
                if route == "ask":
                    if kind == "needs_clarification":
                        report["questions"] = [QUESTIONS.get(f, f) for f in report["first_response"]["fields"]]
                    report.update(status="first_response", message_code="first_response_stop")
                    break
                if route == "completion" and initial:
                    score, invention = q_score(report["first_response"], False, report["task_id"], rubric)
                    report.update(initial_q_score=score, initial_critical_invention=invention)
                    (out/"first-response.json").write_bytes(json.dumps(report["first_response"], ensure_ascii=False).encode("utf-8"))
                    if not score or invention:
                        report.update(message_code="completion_initial_question_miss", completion_not_reached_reason="initial_question_miss")
                        break
                    report.update(questions=[QUESTIONS.get(f, f) for f in report["first_response"]["fields"]])
                    prompt, previous, purpose = completion_text, None, "interpretation"
                    continue
                if kind == "needs_clarification":
                    report.update(message_code="completion_additional_question" if route == "completion" else "clarification_stop")
                    break
                if kind == "unsupported":
                    if budget.stage == "repair" or route != "source": raise ValueError("unsupported_route")
                    report["unsupported_to_source"] = True
                    target, previous, purpose = "source", None, "source"
                    continue
                if fault:
                    candidate = fault.inject(target, candidate)
                    if target == "spec": candidate = cad_spec.validate_spec(candidate)
                    else:
                        candidate = agent.source_from_final(candidate)
                        agent.cad_run.source_contract(ast.parse(candidate))
            except ValueError as exc:
                if initial and report["first_response"].get("raw") is None and target == "spec":
                    try: report["first_response"]["raw"] = cad_spec.read_json(agent.strip_final_fence(final, "json", "spec"))
                    except ValueError: pass
                if route == "ask":
                    report.update(status="first_response", message_code=str(exc)); break
                if route == "completion" and initial:
                    _, invention = q_score(report["first_response"], False, report["task_id"], rubric)
                    report.update(initial_q_score=0, initial_critical_invention=invention,
                        completion_not_reached_reason="invalid_initial_question", message_code=str(exc))
                    (out/"first-response.json").write_bytes(json.dumps(report["first_response"], ensure_ascii=False).encode("utf-8"))
                    break
                if str(exc) in ("private_source", "unsupported_route") or preview or budget.counts["parse_repair"]:
                    raise
                invalid = agent.invalid_feedback(final, str(exc))
                previous, purpose = ({**previous, **invalid} if budget.stage == "repair" else invalid), "parse_repair"
                continue
            if preview:
                report.update(status="preview", message_code="confirmation_required", preview_kind=target)
                (out/("preview-source.py" if target == "source" else "preview-spec.json")).write_text(
                    candidate if target == "source" else cad_spec.canonical(candidate), encoding="utf-8")
                break
            if target == "spec":
                canonical = cad_spec.canonical(candidate)
                if canonical == last_spec: raise ValueError("unchanged_spec")
                last_spec = canonical
                (out/("build-spec-c%d.json" % report['calls'][-1]['call'])).write_text(canonical, encoding="utf-8")
                source = cad_spec.compile_spec(candidate)
            else: source = candidate
            timeout = math.floor(budget.cad_timeout())
            if guard:timeout=min(timeout,math.floor(guard.remaining()))
            if timeout < 1: raise Stop("episode_stage_deadline_exceeded")
            source_path = out/("input-a%d.py" % (budget.attempts+1))
            source_path.write_bytes(source.encode("utf-8"))
            cad_out = out/("a%d-mvp1" % (budget.attempts+1))
            argv = [sys.executable, "-B", str(root/"tools/cad_run.py"), "--script", str(source_path),
                "--out-dir", str(cad_out), "--timeout-s", str(timeout), "--recipe", "freecadcmd", "--probe-profile", "verify-v3",
                "--gold", str(gold_path), "--task", report["task_id"], "--generator", "compiler" if target == "spec" else "agent",
                "--end-to-end-s", str(min(budget.remaining(),guard.remaining() if guard else 900)), "--verification-timeout-s", "90" if budget.stage == "repair" else "300"]
            tick = budget.clock()
            budget.cad()
            completed = runner(argv, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace",
                               shell=False, stdin=subprocess.DEVNULL, timeout=min(budget.remaining(reserve=0),guard.remaining(reserve=0) if guard else 900))
            result = agent.loads(completed.stdout)
            if (not isinstance(result, dict) or result.get("schema") != "cad-harness.cad_run.v0"
                    or result.get("task_id") != report["task_id"] or result.get("probe_profile") != "verify-v3"
                    or result.get("script_sha256") != agent.digest(source) or result.get("gold_sha256") != report["gold_sha256"]
                    or agent.loads((cad_out/"result.json").read_text(encoding="utf-8")) != result):
                raise ValueError("invalid_cad_result")
            report["attempts"].append(dict(attempt=budget.attempts, stage=budget.stage, source_sha256=agent.digest(source),
                out_dir=cad_out.relative_to(root).as_posix(), wall_ms=(budget.clock()-tick)*1000,
                started_elapsed_s=tick-budget.started, ended_elapsed_s=budget.clock()-budget.started,
                build_timeout_s=timeout, reimport_timeout_s=90 if budget.stage == "repair" else 300, result=agent.clean(result)))
            report.update(final_out_dir=report["attempts"][-1]["out_dir"], geometry_ok=result.get("geometry_ok"))
            if budget.clock() > min(budget.deadline, budget.stage_deadline):
                raise Stop("episode_stage_deadline_exceeded")
            if fault:
                fault.observe(result, report['calls'][-1]['call'])
                if fault.record.get("observed") and not fault.record.get("detected"):
                    raise ValueError("fault_false_pass" if result.get("geometry_ok") is True else "fault_detection_mismatch")
            problem = eval_verify.harness_failure(report)
            if problem: raise ValueError(problem)
            if completed.returncode == 0:
                if not eval_verify.result_pass(result): raise ValueError("invalid_cad_success")
                report.update(status="ok", message_code="completed"); break
            reason = agent.repair_reason(result)
            if reason: raise ValueError(reason)
            if budget.attempts != 1:
                report.update(message_code="cad_repair_failed"); break
            report["repair_eligible"] = True
            budget.begin_repair()
            previous, purpose = feedback(target, candidate, result), "repair"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["message_code"] = agent.clean(str(exc)) or type(exc).__name__
    finally:
        report.update(ended_at=agent.utc(), wall_ms=(budget.clock()-budget.started)*1000,
            llm_calls=budget.calls if provider_retry else len(report['calls']),logical_calls=budget.calls,cad_attempts=budget.attempts,budget_counts=budget.counts,
            parse_repairs=budget.counts["parse_repair"], repair_calls=budget.counts["repair"],
            repair_invoked=any(c['purpose']=='repair' for c in report['calls']),repair_success=budget.counts['repair']==1 and report['status']=='ok')
        if provider_retry:
            report.update(transport_attempts=len(report['calls']),provider_rejected_attempts=sum(c['provider_rejected'] for c in report['calls']),
                provider_wait_s=sum(c.get('backoff_s',0) for c in report['calls']))
        if route == "completion" and not report["completion_reached"]:
            report.setdefault("completion_not_reached_reason", report["message_code"] or "initial_question_not_accepted")
        if report["repair_eligible"] and not report['repair_invoked']:
            reason = report["message_code"] or "repair_slot_not_used"
            report["repair_not_attempted_reason"] = reason
            if not any(s in reason for s in ("quota_", "sha_", "agents", "deadline", "reservation", "budget")):
                report["message_code"] = "harness_repair_not_invoked:"+reason
        if report["wall_ms"] >= 900000:
            report.update(status="failed", message_code="episode_deadline_exceeded")
        if guard:
            report["shared_deadline_remaining_s"] = None if guard.deadline is None else max(0, guard.deadline-guard.clock())
            if guard.deadline is not None and guard.clock() >= guard.deadline: report.update(status="failed", message_code="shared_deadline_exceeded")
        with (out/"driver-run.json").open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, allow_nan=False)
    return report, 0 if report["status"] in ("ok", "preview", "first_response") else 1
