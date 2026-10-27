"""H0 durable call pools: each <=40, original development pool never reset."""
import json
import os
from pathlib import Path

from tools import cad_verify_v4_ledger as ledger
from tools.cad_verify_guard import Stop

CAP=40
SCOPE='harness2-solidworks-H0-development40-20261026'


class Pool:
    def __init__(self,root,*,scope=SCOPE):
        if not isinstance(scope,str) or not scope or len(scope)>160:raise Stop('H0_pool_invalid_scope')
        self.scope=scope
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'calls.jsonl';self.lock=None;self.state={};self.sequence=0

    def __enter__(self):
        self.lock=(self.root/'pool.lock').open('x',encoding='utf-8')
        self.lock.write(self.scope);self.lock.flush();os.fsync(self.lock.fileno())
        try:
            if self.path.exists():
                for raw in self.path.read_text(encoding='utf-8').splitlines():
                    row=json.loads(raw)
                    if row['scope']!=self.scope or row['sequence']!=self.sequence+1:raise Stop('H0_pool_corrupt')
                    self.apply(row);self.sequence+=1
            return self
        except BaseException:
            self.__exit__();raise

    def apply(self,row):
        key=row['attempt']
        if row['event']=='reserve':
            if key in self.state or self.used>=CAP:raise Stop('H0_pool_invalid_reservation')
            self.state[key]='pending'
        elif row['event'] in ('charged','verified_rejected'):
            if self.state.get(key)!='pending':raise Stop('H0_pool_invalid_settlement')
            self.state[key]=row['event']
        else:raise Stop('H0_pool_invalid_event')

    @property
    def used(self):return sum(s!='verified_rejected' for s in self.state.values())

    @property
    def remaining(self):return CAP-self.used

    def append(self,event,attempt):
        row=dict(scope=self.scope,sequence=self.sequence+1,event=event,attempt=attempt,at=ledger.utc())
        # Validate transition first without changing the accepted state on an IO error.
        before=dict(self.state)
        try:self.apply(row)
        finally:self.state=before
        raw=(json.dumps(row,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')
        with self.path.open('ab',buffering=0) as f:
            if f.write(raw)!=len(raw):raise Stop('H0_pool_partial_write')
            os.fsync(f.fileno())
        self.apply(row);self.sequence+=1

    def reserve(self,key):
        if self.remaining<=0:raise Stop('H0_development_40_call_cap')
        self.append('reserve',key)

    def settle(self,key,*,rejected=False):
        self.append('verified_rejected' if rejected else 'charged',key)

    def summary(self):
        return dict(scope=self.scope,cap=CAP,conservative_reserved_calls=self.used,
            accepted_or_failed_calls=sum(s=='charged' for s in self.state.values()),
            pending_or_unknown_calls=sum(s=='pending' for s in self.state.values()),
            verified_overload_rejections=sum(s=='verified_rejected' for s in self.state.values()),
            remaining=self.remaining,billing_missing_reason='invoice_not_provided')

    def __exit__(self,*unused):
        if self.lock:self.lock.close();(self.root/'pool.lock').unlink()


class BudgetJournal(ledger.Journal):
    def __init__(self,*args,pool,**kwargs):
        super().__init__(*args,**kwargs);self.pool=pool

    def append(self,event,**fields):
        model=fields.get('operation')=='model'
        key='/'.join((self.run_id,str(fields.get('episode_id')),str(fields.get('attempt_id'))))
        if event=='attempt_started' and model:self.pool.reserve(key)
        row=super().append(event,**fields)
        os.fsync(self.file.fileno())
        if event=='attempt_finished' and model:
            summary=fields.get('provider_summary') or {}
            rejected=(fields.get('provider_rejected') is True and fields.get('charged') is False
                and summary.get('provider_rejected') is True and summary.get('assistant_output') is False
                and summary.get('parse_complete') is True and summary.get('error_infos')
                and set(summary['error_infos'])=={'server_overloaded'})
            if fields.get('charged') is False and not rejected:raise Stop('H0_unverified_charge_exemption')
            self.pool.settle(key,rejected=bool(rejected))
        return row
