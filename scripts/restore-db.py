"""Restore an archived SQLite snapshot into a new local file; never overwrite."""
import argparse,sqlite3
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('destination',type=Path);p.add_argument('--workspace-owner',help='Map a single hosted workspace to this local owner (local-developer for scripts/dev.mjs)');a=p.parse_args()
if not a.snapshot.is_file():p.error('Snapshot does not exist')
if a.destination.exists():p.error('Destination already exists; choose a new file')
with sqlite3.connect(a.snapshot.resolve().as_uri()+'?mode=ro',uri=True) as source:
 if source.execute('PRAGMA integrity_check').fetchone()[0]!='ok':p.error('Snapshot integrity check failed')
 if a.workspace_owner:
  names={r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if 'workspaces' not in names:p.error('--workspace-owner is only for the JavaScript/D1 workspaces schema')
  if source.execute('SELECT count(*) FROM workspaces').fetchone()[0]!=1:p.error('Owner mapping requires exactly one workspace')
 a.destination.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(a.destination) as target:
  source.backup(target)
  if a.workspace_owner:target.execute('UPDATE workspaces SET id=?',(a.workspace_owner,));target.commit()
  assert target.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
print('Restored:',a.destination)
