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


class ComparisonGates(unittest.TestCase):
    def test_cache_exact_boundary_and_integer_precision(self):
        row=lambda n,c:dict(initial_usage=dict(input_tokens=n,cached_input_tokens=c))
        self.assertTrue(h2.cache_match(row(1000,100),row(1000,110))[0])
        self.assertFalse(h2.cache_match(row(1000,100),row(1000,111))[0])
        n=10**24
        self.assertFalse(h2.cache_match(row(n,0),row(n,n//100+1))[0])

    def test_unknown_invalid_or_boolean_cache_is_not_zero(self):
        for n,c in ((None,None),(0,0),(True,0),(100,True),(100,-1),(100,101),(100,1.5)):
            with self.subTest(input=n,cached=c):
                row=dict(initial_usage=dict(input_tokens=n,cached_input_tokens=c))
                self.assertFalse(h2.cache_match(row,row)[0])

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
        self.identity_patch=patch.object(native,'solidworks_identity',return_value={});self.identity_patch.start();self.addCleanup(self.identity_patch.stop)

    def test_insufficient_pair_budget_rolls_to_new_pool_without_spending_old(self):
        exp=self.experiment;phase='comparison';old=runtime.PRIVATE/exp.pool_name(phase,1)
        with Pool(old,scope=exp.pool_scope(phase,1)) as pool:
            for i in range(35):pool.reserve(str(i));pool.settle(str(i))
        with exp.unit_pool('pair-01',phase,h2.plan_trials(phase,'H2D1',1),{}) as (pool,index):
            self.assertEqual(index,2);self.assertEqual(pool.remaining,40)
        with Pool(old,scope=exp.pool_scope(phase,1)) as pool:self.assertEqual(pool.used,35)

    def test_pending_call_is_not_silently_reset_by_another_pool(self):
        exp=self.experiment;phase='comparison'
        with Pool(runtime.PRIVATE/exp.pool_name(phase,1),scope=exp.pool_scope(phase,1)) as pool:pool.reserve('uncertain')
        with self.assertRaises(Stop):
            with exp.unit_pool('pair-01',phase,h2.plan_trials(phase,'H2D1',1),{}):pass
        self.assertFalse((runtime.PRIVATE/exp.pool_name(phase,2)).exists())

    def fake_trial(self,trial,pool,index,phase):
        label=trial['label'];out=runtime.PRIVATE/('h2-unit-'+label);out.mkdir()
        with BudgetJournal(out/'ledger.jsonl',label,phase,pool=pool) as journal:
            fields=dict(operation='model',episode_id=label,attempt_id='one')
            journal.append('attempt_started',**fields)
            journal.append('attempt_finished',**fields,charged=True)
        row=dict(sample(passed=label.endswith(('R1','R2'))),label=label,case=trial['case'],variant=trial['variant'],phase=phase,
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
        with Pool(runtime.PRIVATE/exp.pool_name('comparison',1),scope=exp.pool_scope('comparison',1)) as pool:
            self.assertEqual(pool.used,2)

    def test_cache_exclusions_still_charge_every_attempt_and_do_not_adopt(self):
        exp=self.experiment;exp.trial=self.fake_trial
        result=exp.run()
        self.assertEqual(result['pair_count'],10);self.assertEqual(result['matched_pairs'],0)
        self.assertEqual(result['total_reserved_model_calls'],25)
        self.assertFalse(result['adopted']);self.assertEqual(result['final_holdout_n'],0)
        self.assertEqual(result['reason'],'five_matched_pairs_required')


if __name__=='__main__':unittest.main()
