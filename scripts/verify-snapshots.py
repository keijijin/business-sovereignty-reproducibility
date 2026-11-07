#!/usr/bin/env python3
import hashlib,json,sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
m=json.loads((root/'snapshots/manifest.json').read_text());results=[]
for item in m['files']:
 p=root/item['file'];assert p.stat().st_size==item['bytes'],str(p);assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],str(p)
 results.append({'name':item['file']+' size/SHA-256','status':'passed'})
for p in (root/'snapshots').glob('*.sqlite'):
 with sqlite3.connect(p) as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
rows=json.loads((root/'snapshots/hosted-d1.rows.json').read_text())['rows'];assert all(r['id'].startswith('sample-workspace-') for r in rows)
with sqlite3.connect(root/'snapshots/hosted-d1.sqlite') as db:assert [r[0] for r in db.execute('SELECT id FROM workspaces')]==[r['id'] for r in rows]
results.append({'name':'SQLite integrity and anonymized workspace IDs','status':'passed'})
print(json.dumps({'kind':'snapshot size/hash/integrity verification','passed':len(results),'failed':0,'results':results},ensure_ascii=False,indent=2))
