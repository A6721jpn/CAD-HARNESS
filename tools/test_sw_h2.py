"""Independent consumer regressions. No live model, COM or sealed-data reads."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import sw_h2 as h2,sw_h2_runtime as native,sw_h0_runtime as runtime
from tools import cad_verify_v4_ledger as ledger,cad_verify_v4_agent as agent
from tools.sw_h0_budget import Pool,BudgetJournal
from tools.sw_m1_inputs import PRIVATE
from tools.cad_verify_guard import Stop


def sample(passed=False):
    return dict(passed=passed,critical_invention=False,model_calls=1,active_s=2.)


def cache_counts(uncached,read,writes=0):
    return dict(initial_usage=dict(input_uncached_tokens=uncached,cache_read_tokens=read,cache_write_tokens=writes))


class ComparisonGates(unittest.TestCase):
    def test_cache_exact_boundary_and_integer_precision(self):
        self.assertTrue(h2.cache_match(cache_counts(900,100),cache_counts(890,110))[0])
        self.assertFalse(h2.cache_match(cache_counts(900,100),cache_counts(889,111))[0])
        n=10**24;cached=n//100+1
        self.assertFalse(h2.cache_match(cache_counts(n,0),cache_counts(n-cached,cached))[0])

    def test_unknown_invalid_or_boolean_cache_is_not_zero(self):
        for n,c,w in ((None,None,0),(0,0,0),(True,0,0),(100,True,0),(100,-1,0),(100,1.5,0),(100,50,None),(100,50,-1)):
            with self.subTest(input=n,cached=c,writes=w):
                row=cache_counts(n,c,w)
                self.assertFalse(h2.cache_match(row,row)[0])

    def test_native_cache_hits_larger_than_uncached_input_are_valid(self):
        self.assertTrue(h2.cache_match(cache_counts(100,900),cache_counts(90,910))[0])
        self.assertTrue(h2.cache_match(cache_counts(0,100),cache_counts(0,200))[0])

    def test_cache_write_bucket_participates_in_total_input(self):
        self.assertFalse(h2.cache_match(cache_counts(100,800,100),cache_counts(100,800,0))[0])

    def test_adoption_needs_two_more_passes(self):
        pairs=[dict(A=sample(i<2),B=sample(i<4)) for i in range(5)]
        self.assertTrue(h2.compare(pairs)['eligible'])
        pairs[-2]['B']['passed']=False
        self.assertEqual(h2.compare(pairs)['reason'],'pass_gain_below_two')

    def test_more_passes_do_not_override_time_calls_or_invention(self):
        for key,value,reason in (('active_s',3.,'calls_or_active_time_worse'),
                ('model_calls',2,'calls_or_active_time_worse'),('critical_invention',True,'critical_invention_increased')):
            pairs=[dict(A=sample(i<2),B=sample(i<4)) for i in range(5)]
            pairs[0]['B'][key]=value
            self.assertEqual(h2.compare(pairs)['reason'],reason)

    def test_incomplete_or_missing_measurements_cannot_adopt(self):
        pairs=[dict(A=sample(False),B=sample(True)) for _ in range(5)]
        self.assertFalse(h2.compare(pairs[:4])['eligible'])
        pairs[0]['B']['active_s']=None
        self.assertEqual(h2.compare(pairs)['reason'],'adoption_measurement_missing')

    def test_resume_prefix_preserves_pair_order(self):
        plan=h2.plan_trials('comparison','fixture',1)
        self.assertEqual([r['variant'] for r in h2.pending_trials(plan,{'P01A':{}})],['B'])
        with self.assertRaises(Stop):h2.pending_trials(plan,{'P01B':{}})
        with self.assertRaises(Stop):h2.pending_trials(plan,{'OTHER':{}})


class CustodyGates(unittest.TestCase):
    def test_frontmatter_and_multiple_paragraph_changes_are_rejected(self):
        original=b'---\nname: independent\n---\n\n# Guide\n\nbody one\n\nbody two\n'
        for changed in (original.replace(b'independent',b'new-name'),
                original.replace(b'body one',b'new one').replace(b'body two',b'new two')):
            with self.assertRaises(Stop):native.description_only(original,changed)

    def test_quarantined_dataset_is_refused_before_fixture_read(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            root=Path(temp);(root/'test').mkdir();(root/'test/quarantine.json').write_text('{}')
            with patch.object(native.fixtures,'PUBLIC',root),patch.object(native.fixtures,'admitted',side_effect=AssertionError('must_not_read')):
                with self.assertRaisesRegex(Stop,'H2_dataset_quarantined'):native.context('test')

    def test_mock_manifest_has_no_live_authorization(self):
        with self.assertRaisesRegex(Stop,'H2_live_requires_frozen_manifest'):
            native.isolated_execute('unused',{},None,{'evidence_mode':'unit_mock'},None,None)

    def test_fixture_gate_rejects_gold_request_and_authority_changes(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            path=Path(temp)/'gold.json';path.write_text('{}')
            gold=dict(provenance=dict(authority='fixture',confirmed=False))
            entry=dict(case='independent',gold_path=str(path),gold_sha256=ledger.file_sha(path),gold=gold,
                request_sha256='bound-request',route='spec',max_calls=3)
            with patch.object(native,'context',return_value=(None,[entry],{})):
                for bad in (dict(entry,request_sha256='different'),dict(entry,max_calls=4),dict(entry,route='source')):
                    with self.assertRaises(Stop):native.fixture_admission('unit',bad,gold,path)
                changed=copy.deepcopy(gold);changed['provenance']=dict(authority='human',confirmed=True)
                with self.assertRaises(Stop):native.fixture_admission('unit',entry,changed,path)
                with self.assertRaises(Stop):native.fixture_admission('unit',entry,dict(gold,unexpected=True),path)

    def test_driver_admission_is_still_enforced_not_removed(self):
        source='def run_driver(gold,gold_path,preview=False):\n'+''.join('    '+line+'\n' for line in native.GATE.splitlines())+'    return True\n'
        tree,_=native.adapted_tree(source)
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            path=Path(temp)/'gold.json';path.write_text('{}')
            gold=dict(provenance=dict(authority='fixture',confirmed=False))
            expected=dict(case='independent',gold_path=str(path),gold_sha256=ledger.file_sha(path),gold=gold,
                request_sha256='bound-request',route='spec',max_calls=3)
            scope={'_h2_fixture_admission':lambda g,p:native.fixture_admission('unit',dict(expected,request_sha256='changed'),g,p)}
            exec(compile(tree,'independent-fixture-driver','exec'),scope)
            with patch.object(native,'context',return_value=(None,[expected],{})):
                with self.assertRaises(Stop):scope['run_driver'](gold,path)

    def test_unrecognized_production_gate_fails_closed(self):
        with self.assertRaises(Stop):native.adapted_tree('def run_driver():\n    return True\n')

    def test_repair_observations_never_forward_expected_values_or_subcheck_names(self):
        previous=dict(result=dict(measurements=dict(original_geometry_pass=False,reference_secret_coordinate=98765.4321),
            predicate_details=dict(checks=[dict(field='holes',passed=False,sub_checks=[dict(id='reference_secret_coordinate',expected=98765.4321)])])))
        adapter=runtime.SafeAdapter(b'independent-guide','independent-request')
        context=adapter.developer_context(None,'spec',previous)
        data=json.loads(context.split(agent.MARKER,1)[1])
        encoded=json.dumps(data)
        self.assertNotIn('98765.4321',encoded)
        self.assertNotIn('reference_secret_coordinate',encoded)

    def test_resolved_user_packet_rejects_filename_and_arm_headers(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            root=Path(temp);payload=root/'payload.json';stdout=root/'stdout.bin'
            packet=dict(request='Independent fixture request',runtime_data=dict(target='spec'))
            ledger.write_json(payload,packet)
            text=json.dumps(packet)
            def emit(value):
                stdout.write_text(json.dumps(dict(type='message_end',message=dict(role='user',content=[dict(type='text',text=value)])))+'\n',encoding='utf-8')
            emit(text)
            self.assertTrue(native.user_packet_matches(stdout,payload))
            emit('<file path="run-P01B/payload.json">'+text+'</file>')
            self.assertFalse(native.user_packet_matches(stdout,payload))

    def test_prompt_verification_needs_unchanged_user_data_not_an_assistant_echo(self):
        with tempfile.TemporaryDirectory(dir=PRIVATE) as temp:
            root=Path(temp);payload=root/'payload.json'
            packet=dict(request='Independent fixture request',runtime_data=dict(target='spec'))
            ledger.write_json(payload,packet)
            for index,(role,value) in enumerate((('assistant',packet),
                    ('user',dict(packet,request='Changed requirement')),
                    ('user',dict(packet,trial_label='P01B')))):
                stdout=root/(str(index)+'.bin')
                stdout.write_text(json.dumps(dict(type='message_end',message=dict(role=role,
                    content=[dict(type='text',text=json.dumps(value))])))+'\n',encoding='utf-8')
                self.assertFalse(native.user_packet_matches(stdout,payload))


class NeutralTimeoutSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=PRIVATE);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.identity=dict(pid=123,revision='independent',documents=0)
        self.com=dict(status='PASS',stop=False,COM_state_unknown=False,final_documents=0,pid=123,revision='independent')
        self.path=self.root/'com-result.json';self.path.write_text(json.dumps(self.com))
        self.ready=patch.object(native,'solidworks_identity',return_value=self.identity)
        self.ready.start();self.addCleanup(self.ready.stop)

    def test_unknown_open_or_different_native_state_cannot_certify_timeout(self):
        for change in (dict(stop=True),dict(COM_state_unknown=True),dict(final_documents=1),
                dict(final_documents=False),dict(pid=456),dict(status='FAIL')):
            self.path.write_text(json.dumps(dict(self.com,**change)))
            self.assertIsNone(native.neutral_timeout_certificate(self.root,self.identity))
        self.path.write_text(json.dumps(self.com))
        with patch.object(native,'solidworks_identity',return_value=dict(self.identity,documents=1)):
            self.assertIsNone(native.neutral_timeout_certificate(self.root,self.identity))

    def test_closed_native_sdk_timeout_remains_exception_but_is_not_SW_nonresponse(self):
        transport=native.Transport.__new__(native.Transport);transport.manifest=dict(solidworks=self.identity)
        argv=['python','cad','--out-dir',str(self.root)]
        with patch.object(native._TRANSPORT_BASE,'_invoke',side_effect=Stop('H0_neutral_worker_timeout')):
            with self.assertRaisesRegex(Stop,'H0_neutral_worker_timeout'):transport._invoke(argv)
        self.assertEqual(transport.fatal,'H2_closed_SW_neutral_timeout')
        self.assertFalse(transport.manifest.get('_native_uncertain',False))
        self.assertFalse(transport.manifest['_known_episode_timeout']['scored_pass'])

    def test_other_failures_never_use_closed_document_as_a_bypass(self):
        for reason in ('STOP_SW_nonresponse_no_restart','STOP_SW_state_unknown_no_restart','H0_frozen_file_changed'):
            transport=native.Transport.__new__(native.Transport);transport.manifest=dict(solidworks=self.identity)
            with patch.object(native._TRANSPORT_BASE,'_invoke',side_effect=Stop(reason)):
                with self.assertRaises(Stop):transport._invoke(['python','cad','--out-dir',str(self.root)])
            self.assertTrue(transport.manifest['_native_uncertain'])
            self.assertNotIn('_known_episode_timeout',transport.manifest)


class DurableSchedule(unittest.TestCase):
    def setUp(self):
        PRIVATE.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=PRIVATE);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.patcher=patch.object(runtime,'PRIVATE',self.root/'private');self.patcher.start();self.addCleanup(self.patcher.stop)
        runtime.PRIVATE.mkdir()
        self.experiment=h2.Experiment.__new__(h2.Experiment)
        self.experiment.name='unit';self.experiment.out=self.root/'experiment';self.experiment.out.mkdir()
        self.experiment.pub=self.root/'public';self.experiment.pub.mkdir()
        self.experiment.identity='test-commitment';self.experiment.native_uncertain=False
        self.experiment.shared=dict(development_ids=['H2D1'],holdout_ids=['H2H1'],solidworks={},generator=dict(model='unit',thinking='unit'))
        self.experiment.shared['funding']=dict(maximum_logical_calls=40,pools=[
            dict(name='h2-unit-epoch-pool-01',scope='harness2-solidworks-H2-unit-epoch-01',starting_reserved=0)])
        self.identity_patch=patch.object(native,'solidworks_identity',return_value={});self.identity_patch.start();self.addCleanup(self.identity_patch.stop)

    def test_insufficient_pair_budget_stops_without_spending_or_opening_another_pool(self):
        exp=self.experiment;old=runtime.PRIVATE/exp.pool_name()
        with Pool(old,scope=exp.pool_scope()) as pool:
            for i in range(35):pool.reserve(str(i));pool.settle(str(i))
        with self.assertRaisesRegex(Stop,'H2_authorized_call_cap'):
            exp.unit('pair-01','comparison',h2.plan_trials('comparison','H2D1',1))
        self.assertFalse((exp.out/'unit-pair-01.json').exists())
        self.assertEqual(list(exp.pub.iterdir()),[])
        with Pool(old,scope=exp.pool_scope()) as pool:self.assertEqual(pool.used,35)

    def test_pending_call_is_not_silently_reset_by_another_pool(self):
        exp=self.experiment;phase='comparison'
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:pool.reserve('uncertain')
        with self.assertRaises(Stop):
            with exp.unit_pool('pair-01',phase,h2.plan_trials(phase,'H2D1',1),{}):pass
        self.assertFalse((exp.out/'unit-pair-01.json').exists())

    def fake_trial(self,trial,pool,phase):
        label=trial['label'];out=runtime.PRIVATE/('h2-unit-'+label);out.mkdir()
        with BudgetJournal(out/'ledger.jsonl',label,phase,pool=pool) as journal:
            for index in range(getattr(self,'calls_per_trial',1)):
                fields=dict(operation='model',episode_id=label,attempt_id=str(index+1))
                journal.append('attempt_started',**fields)
                journal.append('attempt_finished',**fields,charged=True)
        values=sample(passed=label.endswith(('R1','R2')));values['model_calls']=getattr(self,'calls_per_trial',1)
        row=dict(values,label=label,case=trial['case'],variant=trial['variant'],phase=phase,
            experiment_manifest_sha256=self.experiment.identity,ledger_sha256=ledger.file_sha(out/'ledger.jsonl'),stopped=False,
            completed=True,wall_s=2.,cad_attempts=1,repair_calls=0,initial_usage=None,
            initial_payload_sha256=ledger.sha(trial['case'].encode()))
        ledger.write_json(out/'trial-result.json',row);ledger.write_json(self.experiment.pub/(label+'.json'),row)
        return row

    def test_half_pair_resume_keeps_A_and_charges_only_unfinished_B(self):
        exp=self.experiment;plan=h2.plan_trials('comparison','H2D1',1)
        def interrupted(trial,*args):
            if trial['variant']=='B':raise OSError('simulated-controller-interruption')
            return self.fake_trial(trial,*args)
        exp.trial=interrupted
        with self.assertRaises(OSError):exp.unit('pair-01','comparison',plan)
        a=runtime.PRIVATE/'h2-unit-P01A/trial-result.json';before=ledger.file_sha(a)
        exp.trial=self.fake_trial
        rows=exp.unit('pair-01','comparison',plan)
        self.assertEqual([r['variant'] for r in rows],['A','B']);self.assertEqual(ledger.file_sha(a),before)
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:
            self.assertEqual(pool.used,2)

    def test_cache_exclusions_still_charge_every_attempt_and_do_not_adopt(self):
        exp=self.experiment;exp.trial=self.fake_trial
        result=exp.run()
        self.assertEqual(result['pair_count'],10);self.assertEqual(result['matched_pairs'],0)
        self.assertEqual(result['total_reserved_model_calls'],25)
        self.assertFalse(result['adopted']);self.assertEqual(result['final_holdout_n'],0)
        self.assertEqual(result['reason'],'five_matched_pairs_required')

    def test_budget_across_calibration_and_pairs_ends_inconclusive_before_half_pair(self):
        exp=self.experiment;self.calls_per_trial=2;exp.trial=self.fake_trial
        result=exp.run()
        self.assertEqual(result['reason'],'authorized_call_budget_exhausted')
        self.assertFalse(result['adopted']);self.assertEqual(result['final_holdout_n'],0)
        self.assertEqual(result['pair_count'],7);self.assertEqual(result['total_reserved_model_calls'],38)
        self.assertFalse((exp.out/'unit-pair-08.json').exists())
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:
            self.assertEqual(pool.used,38);self.assertEqual(pool.remaining,2)
            self.assertEqual(pool.summary()['pending_or_unknown_calls'],0)

    def test_full_final_block_is_not_started_on_a_partial_budget(self):
        exp=self.experiment;exp.trial=self.fake_trial
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:
            for i in range(26):pool.reserve(str(i));pool.settle(str(i))
        final=h2.plan_trials('final',['H2H'+str(i) for i in range(1,6)])
        with self.assertRaisesRegex(Stop,'H2_authorized_call_cap'):exp.unit('final','final',final)
        self.assertEqual(list(exp.pub.iterdir()),[])

    def carried_funding(self,used=17):
        exp=self.experiment
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:
            for i in range(used):pool.reserve('prior-'+str(i));pool.settle('prior-'+str(i))
            prefix=pool.path.read_bytes()
        exp.shared['funding']['pools'][0].update(starting_reserved=used,prefix_bytes=len(prefix),prefix_sha256=ledger.sha(prefix))
        exp.shared['funding']['pools'].append(dict(name='fallback-pool',scope='new40',starting_reserved=0))
        exp.shared['funding']['maximum_logical_calls']=150
        return prefix

    def test_carry_is_spent_first_and_fallback_preserves_old_reservations(self):
        exp=self.experiment;prefix=self.carried_funding();exp.trial=self.fake_trial
        exp.unit('pair-01','comparison',h2.plan_trials('comparison','H2D1',1))
        self.assertFalse((runtime.PRIVATE/exp.pool_name(2)).exists())
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:
            self.assertEqual(pool.used,19)
            for i in range(17):pool.reserve('current-'+str(i));pool.settle('current-'+str(i))
        exp.unit('pair-02','comparison',h2.plan_trials('comparison','H2D1',2))
        with Pool(runtime.PRIVATE/exp.pool_name(),scope=exp.pool_scope()) as pool:
            self.assertEqual(pool.used,36);self.assertEqual(pool.path.read_bytes()[:len(prefix)],prefix)
        with Pool(runtime.PRIVATE/exp.pool_name(2),scope=exp.pool_scope(2)) as pool:self.assertEqual(pool.used,2)

    def test_unsettled_fallback_cannot_be_bypassed_by_available_carry(self):
        exp=self.experiment;self.carried_funding()
        with Pool(runtime.PRIVATE/exp.pool_name(2),scope=exp.pool_scope(2)) as pool:pool.reserve('unknown')
        with self.assertRaisesRegex(Stop,'H2_unsettled_pool_call'):
            exp.unit('pair-01','comparison',h2.plan_trials('comparison','H2D1',1))
        self.assertEqual(list(exp.pub.iterdir()),[])

    def test_changed_carried_prefix_stops_before_any_new_call(self):
        exp=self.experiment;self.carried_funding()
        path=runtime.PRIVATE/exp.pool_name()/'calls.jsonl';raw=path.read_bytes();path.write_bytes(raw.replace(b'prior-0',b'prior-X',1))
        with self.assertRaisesRegex(Stop,'H2_carry_prefix_changed'):
            exp.unit('pair-01','comparison',h2.plan_trials('comparison','H2D1',1))
        self.assertFalse((runtime.PRIVATE/exp.pool_name(2)).exists())

    def test_interrupted_fallback_pair_resumes_its_own_pool_without_regenerating_A(self):
        exp=self.experiment;self.carried_funding(35);plan=h2.plan_trials('comparison','H2D1',1)
        def interrupted(trial,*args):
            if trial['variant']=='B':raise OSError('simulated-interruption')
            return self.fake_trial(trial,*args)
        exp.trial=interrupted
        with self.assertRaises(OSError):exp.unit('pair-01','comparison',plan)
        a=runtime.PRIVATE/'h2-unit-P01A/trial-result.json';before=ledger.file_sha(a)
        exp.trial=self.fake_trial;exp.unit('pair-01','comparison',plan)
        self.assertEqual(ledger.file_sha(a),before)
        with Pool(runtime.PRIVATE/exp.pool_name(2),scope=exp.pool_scope(2)) as pool:self.assertEqual(pool.used,2)
    def test_certified_old_failed_score_is_retained_and_cannot_be_promoted(self):
        exp=self.experiment;trial=dict(label='CH2D1R1',case='H2D1',variant='A')
        with Pool(runtime.PRIVATE/'resume-test-pool',scope='resume-unit') as pool:
            row=self.fake_trial(trial,pool,'calibration')
        path=runtime.PRIVATE/'h2-unit-CH2D1R1/trial-result.json'
        row.update(passed=False,stopped=True);path.write_text(json.dumps(row))
        old=exp.identity;exp.identity='new-manifest'
        exp.shared['resume']=dict(safe_timeout_label=trial['label'],prefix={trial['label']:dict(
            old_manifest_sha256=old,result_sha256=ledger.file_sha(path))})
        recovered=exp.completed(trial)
        self.assertFalse(recovered['passed']);self.assertTrue(recovered['stopped'])
        row['passed']=True;path.write_text(json.dumps(row))
        with self.assertRaises(Stop):exp.completed(trial)

    def test_continuation_refuses_changed_judge_or_policy_before_reading_prefix(self):
        exp=self.experiment;folder=runtime.PRIVATE/'h2-unit';folder.mkdir()
        critical=('policy_sha256','generator','host','solidworks','runtime_files','OMP_PROFILE','generator_config_sha256',
            'skill_sha256','fixture_admission','transport_adaptation','generation_cwd','protocol','development_ids','holdout_ids')
        old={key:'unchanged' for key in critical}
        old.update(schema='harness2.solidworks.skill.freeze.v3',experiment='unit',evidence_mode='live',input_files={},
            files={'tools/sw_m1_judge.py':'original-judge'})
        ledger.write_json(folder/'experiment-manifest.json',old)
        ledger.write_json(folder/'experiment-SHA256.json',dict(manifest_sha256=ledger.file_sha(folder/'experiment-manifest.json')))
        for changed in (dict(files={'tools/sw_m1_judge.py':'changed-judge'}),dict(policy_sha256='changed-policy')):
            with self.assertRaises(Stop):native.continuation_prefix('unit',[],{},dict(old,**changed))



if __name__=='__main__':unittest.main()
