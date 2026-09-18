"""C1-to-C3 bridge: five parsed sources plus fourteen explicit sample objects."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from build_baseline import compile_documents

ROOT = Path(__file__).parents[1]


def compile_knowledge(data_dir: Path = ROOT / 'data') -> list[dict]:
    documents = json.loads((data_dir / 'knowledge.json').read_text(encoding='utf-8'))
    raw = {doc['id']: doc for doc in compile_documents(data_dir / 'raw/manifest.json')}
    authored = {doc['id']: doc for doc in documents}
    if len(authored) != len(documents) or not raw.keys() <= authored.keys():
        raise ValueError('duplicate or unknown raw-source object identity')
    result = []
    for document in documents:
        if not isinstance(document.get('tenant'), str) or not document['tenant'].strip():
            raise ValueError('knowledge tenant is required')
        if not isinstance(document.get('acl'), list) or any(
            not isinstance(role, str) or not role.strip() for role in document['acl']
        ):
            raise ValueError('knowledge ACL must be a list of exact role strings')
        replacement = raw.get(document['id'])
        if replacement:
            for field in ('entity_type', 'tenant', 'kind'):
                if replacement[field] != document[field]:
                    raise ValueError(f'raw-source identity mismatch: {document["id"]}.{field}')
            # Preserve explicit business attributes (e.g. policy regions), while
            # text, ACL, versions, hashes and lineage come from the raw compiler.
            document = {**document, **replacement}
        result.append(document)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--output', type=Path, default=ROOT / 'generated/knowledge.json')
    args = parser.parse_args()
    documents = compile_knowledge(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(documents, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'objects':len(documents),'compiled_sources':5,'output':str(args.output)}))


if __name__ == '__main__': main()
