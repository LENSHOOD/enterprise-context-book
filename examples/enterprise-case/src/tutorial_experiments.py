"""Run an input-change exercise and a small, deterministic retrieval ablation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from northstar import NorthstarPlatform, Principal, DEFAULT_FIXTURE_TIME

ROOT = Path(__file__).parents[1]


def change_exercise():
    baseline = NorthstarPlatform()
    reader = Principal('learner', 'support')
    with tempfile.TemporaryDirectory() as temp:
        data = Path(temp)/'data'
        shutil.copytree(ROOT/'data',data)
        policy = data/'raw/business/order-cancellation.md'
        policy.write_text(policy.read_text(encoding='utf-8')+'\n新增核验说明：checkpointalpha。\n',encoding='utf-8')
        changed = NorthstarPlatform(data)
        hits = changed.search('checkpointalpha',reader)
        result = {'before_manifest':baseline.manifest,'after_manifest':changed.manifest,
                  'changed_evidence':[h['id'] for h in hits],
                  'wiki_updated':'checkpointalpha' in json.dumps(changed.build_wiki(reader),ensure_ascii=False)}
        assert result['before_manifest'] != result['after_manifest']
        assert result['changed_evidence'] == ['product-cancellation-policy']
        assert result['wiki_updated']
        return result


def ablation():
    platform = NorthstarPlatform()
    questions = json.loads((ROOT/'data/golden-questions.json').read_text())
    # Restrict this measurement to search questions with required evidence.
    questions = [q for q in questions if q['mode'] in ('search','search_any')]
    rows=[]
    for name,disabled in [('bm25',{'semantic_proxy'}),('semantic_proxy',{'bm25'}),('fusion',set())]:
        scores=[]
        for q in questions:
            hits=platform.search(q['question'],Principal('learner',q['role']),limit=5,
                                 disabled_channels=disabled,valid_at=q.get('valid_at'),observed_at=q.get('observed_at'))
            found={h['id'] for h in hits}; expected=set(q['expected_ids'])
            scores.append({'id':q['id'],'bucket':q['bucket'],'evidence_recall_at_5':len(found&expected)/len(expected),
                           'contract_pass':bool(found&expected) if q['mode']=='search_any' else expected<=found})
        rows.append({'channels':name,'questions':len(scores),
                     'mean_evidence_recall_at_5':round(sum(s['evidence_recall_at_5'] for s in scores)/len(scores),4),
                     'contracts_passed':sum(s['contract_pass'] for s in scores),'details':scores})
    return {'manifest':platform.manifest,'clock':DEFAULT_FIXTURE_TIME.isoformat(),
            'warning':'Teaching search-only dataset; proxy is not an embedding model. No production quality claim.',
            'results':rows}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exercise',choices=['change','ablation'])
    args=parser.parse_args()
    print(json.dumps(change_exercise() if args.exercise=='change' else ablation(),ensure_ascii=False,indent=2))
