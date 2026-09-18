"""Regression cases found in the September whole-book audit."""
import json
from pathlib import Path
import sys
import unittest
import shutil
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parents[1] / 'src'))
from northstar import NorthstarPlatform, Principal


class ReviewRegressionTest(unittest.TestCase):
    def setUp(self):
        self.sre = Principal('assigned', 'sre')
        self.other = Principal('outsider', 'support', 'another-tenant')
        self.commander = Principal('commander', 'incident_commander')
        self.platform = NorthstarPlatform()

    def test_context_does_not_expose_other_tenant_or_nonmember_task(self):
        self.platform.begin_diagnosis('SAME-ID', self.sre)
        for outsider in (self.other, Principal('coworker', 'sre'), self.commander):
            package = self.platform.context('退款', outsider, 'SAME-ID')
            self.assertEqual([], package['memories'])
            self.assertEqual('opened', package['task_state'])

    def test_expired_observation_cannot_enter_context_or_preview(self):
        self.platform.begin_diagnosis('STALE', self.sre)
        self.platform.runtime['refund-queue']['observed_at'] = '2020-01-01T00:00:00Z'
        package = self.platform.context('退款', self.sre, 'STALE', runtime_resource='refund-queue')
        self.assertEqual([], package['observations'])
        self.assertEqual(['refund-queue'], package['missing'])
        with self.assertRaises((ValueError, PermissionError)):
            self.platform.prepare_replay('STALE', 'refund-queue', self.sre)

    def test_fabricated_receipt_does_not_resolve_unexecuted_task(self):
        self.platform.begin_diagnosis('FORGED', self.sre)
        forged = dict(receipt_id='receipt:never', task_id='FORGED', target_queue='refund-queue',
                      before_queue_depth=1000, baseline_error_rate=1.0,
                      executed_by='assigned', tenant='northstar')
        with self.assertRaises((ValueError, PermissionError)):
            self.platform.verify_replay(forged, self.sre)
        self.assertEqual(0, self.platform.execution_count)

    def test_current_search_and_wiki_do_not_default_to_historical_policy(self):
        support = Principal('support', 'support')
        ids = {x['id'] for x in self.platform.search('旧规则 出库 取消', support, limit=50)}
        self.assertNotIn('product-cancellation-policy-v1', ids)
        inputs = [c for page in self.platform.build_wiki(support) for c in page['inputs']]
        self.assertFalse(any('policy/order-cancellation@2026-01-01' in c for c in inputs))

    def test_same_task_id_can_be_owned_independently_in_two_tenants(self):
        foreign_sre = Principal('assigned', 'sre', 'another-tenant')
        self.platform.begin_diagnosis('ID', self.sre)
        self.platform.begin_diagnosis('ID', foreign_sre)
        self.platform.memory.append('ID', {'secret':'private'}, self.sre)
        self.assertEqual(1, len(self.platform.memory.read('ID', foreign_sre)))
        with self.assertRaises(PermissionError):
            self.platform.memory.append('ID', {'forged':True}, self.commander)

    def test_returned_memory_and_preview_are_copies(self):
        self.platform.begin_diagnosis('COPY', self.sre)
        events = self.platform.memory.read('COPY', self.sre)
        events[0]['actor'] = 'forged'
        self.assertEqual('assigned', self.platform.memory.read('COPY', self.sre)[0]['actor'])
        preview = self.platform.prepare_replay('COPY', 'refund-queue', self.sre)
        preview['message_count'] = 842
        token = self.platform.confirm(preview['preview_id'], self.commander)
        receipt = self.platform.execute_replay(token, 'copy', self.sre)
        self.assertEqual(100, receipt['replayed'])

    def test_modified_receipt_is_rejected_and_original_can_be_verified_once(self):
        self.platform.begin_diagnosis('MODIFIED', self.sre)
        preview = self.platform.prepare_replay('MODIFIED', 'refund-queue', self.sre)
        token = self.platform.confirm(preview['preview_id'], self.commander)
        receipt = self.platform.execute_replay(token, 'key', self.sre)
        changed = {**receipt, 'before_queue_depth':10000}
        with self.assertRaises(PermissionError): self.platform.verify_replay(changed, self.sre)
        with self.assertRaises(PermissionError): self.platform.verify_replay(receipt, self.other)
        self.assertEqual('verifying', self.platform.task_state('MODIFIED', self.sre))
        self.assertTrue(self.platform.verify_replay(receipt['receipt_id'], self.sre)['verified'])
        with self.assertRaises(ValueError): self.platform.verify_replay(receipt, self.sre)

    def test_clock_advance_and_future_sample_block_actions(self):
        now = [datetime(2026,8,27,10,tzinfo=timezone.utc)]
        platform = NorthstarPlatform(clock=lambda:now[0])
        platform.begin_diagnosis('TTL', self.sre)
        now[0] += timedelta(seconds=60)
        self.assertIsNone(platform.get_status('refund-queue',self.sre))
        with self.assertRaises(PermissionError): platform.prepare_replay('TTL','refund-queue',self.sre)
        platform.runtime['refund-queue']['observed_at']=(now[0]+timedelta(seconds=1)).isoformat()
        self.assertIsNone(platform.get_status('refund-queue',self.sre))

    def test_verification_needs_fresh_post_execution_observation(self):
        now = [datetime(2026,8,27,10,tzinfo=timezone.utc)]
        platform = NorthstarPlatform(clock=lambda:now[0])
        platform.begin_diagnosis('V',self.sre)
        preview=platform.prepare_replay('V','refund-queue',self.sre)
        token=platform.confirm(preview['preview_id'],self.commander)
        receipt=platform.execute_replay(token,'v',self.sre)
        now[0]+=timedelta(seconds=60)
        with self.assertRaises(PermissionError): platform.verify_replay(receipt,self.sre)
        self.assertEqual('verifying',platform.task_state('V',self.sre))

    def test_historical_query_and_wiki_use_the_same_time_window(self):
        support=Principal('reader','support')
        window=dict(valid_at='2026-07-20T00:00:00Z',observed_at='2026-08-27T00:00:00Z')
        hits=self.platform.search('取消规则',support,**window)
        self.assertEqual({'product-cancellation-policy-v1'},{x['id'] for x in hits if x['kind']=='policy'})
        inputs=[x for p in self.platform.build_wiki(support,**window) for x in p['inputs']]
        self.assertTrue(any('@2026-01-01' in x for x in inputs))
        self.assertFalse(any('order-cancellation@2026-08-10' in x for x in inputs))

    def test_raw_source_changes_flow_into_runtime_and_wiki(self):
        with tempfile.TemporaryDirectory() as temp:
            data=Path(temp)/'data'
            shutil.copytree(Path(__file__).parents[1]/'data',data)
            path=data/'raw/business/order-cancellation.md'
            path.write_text(path.read_text()+'\n退款核验标记 checkpointalpha\n')
            platform=NorthstarPlatform(data)
            self.assertNotEqual(self.platform.manifest,platform.manifest)
            hits=platform.search('checkpointalpha',Principal('reader','support'))
            self.assertEqual('product-cancellation-policy',hits[0]['id'])
            self.assertIn('checkpointalpha',json.dumps(platform.build_wiki(Principal('reader','support'))))


if __name__ == '__main__':
    unittest.main()
