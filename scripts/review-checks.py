#!/usr/bin/env python3
"""Reproducible loopback checks. Owns and stops only the servers it starts."""
import copy,hashlib,json,os,socket,subprocess,sys,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
NODE=os.environ.get('NODE_BIN','node');folder=ROOT/'.local'/('review-'+str(time.time_ns()));folder.mkdir(parents=True)
children=[];results=[]
def start(kind,name,spec=None):
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 env=os.environ.copy();env['LOCAL_MEDIA_DIR']=str(folder/(name+'-media'))
 if spec:env['BUSINESS_SPEC']=str(spec)
 cmd=[NODE,'scripts/dev.mjs',str(port),str(folder/(name+'.sqlite'))] if kind=='js' else [sys.executable,'materials/python_server.py',str(port),str(folder/(name+'.sqlite'))]+(['--spec',str(spec)] if spec else [])
 log=open(folder/(name+'.log'),'w');p=subprocess.Popen(cmd,stdout=log,stderr=log,env=env);children.append((p,log));base='http://127.0.0.1:'+str(port)
 for _ in range(100):
  if p.poll() is not None:raise RuntimeError((folder/(name+'.log')).read_text())
  try:
   if call(base,'/api/state')[0]==200:return base
  except OSError:pass
  time.sleep(.05)
 raise RuntimeError('server startup timeout')
def call(base,path,body=None,actor='kai'):
 req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','X-Demo-Actor':actor})
 try:
  with urllib.request.urlopen(req,timeout=60) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as r:return r.code,json.load(r)
def state(base):return call(base,'/api/state')[1]
def post(base,path,**body):return call(base,path,{'revision':state(base)['revision'],**body})
def eq(a,b):assert a==b,f'{str(a)[:200]} != {str(b)[:200]}'
def check(name,fn):
 try:fn();results.append({'name':name,'status':'passed'})
 except Exception as e:results.append({'name':name,'status':'failed','error':str(e)})
def section(entries,kind):return {'kind':kind,'passed':sum(e['status']=='passed' for e in entries),'failed':sum(e['status']=='failed' for e in entries),'results':entries}
try:
 evidence=json.loads((ROOT/'content/evidence.json').read_text());evidence['runs']=[]
 for kind in ['js','py']:
  base=start(kind,'acceptance-'+kind);p=subprocess.run([sys.executable,'materials/acceptance.py',base],capture_output=True,text=True)
  run=json.loads(p.stdout);run['label']={'js':'JavaScript / Node SQLite','py':'Python / SQLite'}[kind];evidence['runs'].append(run)
 # Exercise both export directions, including attrs, roles, withdrawn and policy audits.
 mark=len(results)
 for source,target in [('js','py'),('py','js')]:
  a=start(source,'source-'+source);b=start(target,'target-'+target);part='BRK-001 ブラケット 改訂A'
  _,r=post(a,'/api/requests',title='😀'*120,part=part,reason='変更理由');rid=r['request']['id']
  post(a,'/api/requests/'+rid,title='訂正😀',part=part,reason='訂正理由');post(a,'/api/requests/'+rid+'/withdraw');post(a,'/api/policy',version=1)
  pack=call(a,'/api/export')[1]
  check(source+' → '+target+' import',lambda:eq(post(b,'/api/import',pack=pack)[0],200))
  restored=call(b,'/api/export')[1]
  check(source+' → '+target+' 全申請・属性・履歴一致',lambda:eq(restored['requests'],pack['requests']))
  check(source+' → '+target+' 仕様監査一致',lambda:eq(restored['policyHistory'],pack['policyHistory']))
 evidence['migration']=section(results[mark:],'bidirectional HTTP export/import; fresh destinations')
 mark=len(results)
 for kind in ['js','py']:
  base=start(kind,'large-'+kind);part='BRK-001 ブラケット 改訂A'
  for i in range(200):
   status,out=post(base,'/api/requests',title='😀'*120,part=part,reason='😀'*2000)
   if status!=201:raise RuntimeError(f'{kind} create {i}: {status} {out}')
  status,pack=call(base,'/api/export');encoded=json.dumps(pack,ensure_ascii=False).encode()
  check(kind+' 200件・1MiB超の保存と読出し',lambda:(eq(status,200),eq(len(pack['requests']),200),eq(len(encoded)>1048576,True)))
  before=state(base)
  check(kind+' 201件目を拒否して状態保持',lambda:(eq(post(base,'/api/requests',title='上限',part=part,reason='理由')[0],409),eq(state(base),before)))
  dest=start('py' if kind=='js' else 'js','large-target-'+kind)
  check(kind+' 大容量パックを別実装へ移行',lambda:(eq(post(dest,'/api/import',pack=pack)[0],200),eq(call(dest,'/api/export')[1]['requests'],pack['requests'])))
 evidence['regressions']=section(results[mark:],'200 records, Unicode maximum fields, above former 1MiB IPC cap')
 mark=len(results)
 spec=json.loads((ROOT/'materials/business.json').read_text());spec['fields']['title']=3;spec['parts'].append('TEST-NEW');custom=folder/'custom.json';custom.write_text(json.dumps(spec))
 for kind in ['js','py']:
  base=start(kind,'configured-'+kind,custom)
  check(kind+' 仕様JSONの文字数・部品変更が実行時に反映',lambda:(eq(post(base,'/api/requests',title='😀😀😀',part='TEST-NEW',reason='理由')[0],201),eq(post(base,'/api/requests',title='😀😀😀😀',part='TEST-NEW',reason='理由')[0],400)))
 invalid=copy.deepcopy(spec);invalid['states']=['unsupported'];bad=folder/'invalid.json';bad.write_text(json.dumps(invalid))
 for kind in ['js','py']:
  env=os.environ.copy();env['BUSINESS_SPEC']=str(bad)
  cmd=[NODE,'scripts/dev.mjs','0',str(folder/'bad-js.sqlite')] if kind=='js' else [sys.executable,'materials/python_server.py','0',str(folder/'bad-py.sqlite'),'--spec',str(bad)]
  p=subprocess.run(cmd,env=env,capture_output=True,timeout=10)
  check(kind+' 未対応仕様で起動を拒否',lambda:eq(p.returncode!=0,True))
 evidence['specConfiguration']=section(results[mark:],'startup JSON configuration behavior; changed limit and added part')
 mark=len(results)
 base=start('js','upload-check');video=ROOT/'media/unit-01.mp4';before_hash=hashlib.sha256(video.read_bytes()).hexdigest();raw=b'\x00\x00\x00\x20ftyp'+b'0'*24
 req=urllib.request.Request(base+'/api/media/01',data=raw,method='PUT',headers={'Content-Type':'video/mp4'})
 with urllib.request.urlopen(req) as response:status=response.status
 check('ローカル動画取込はGit動画を保持し専用領域へ保存',lambda:(eq(status,200),eq(hashlib.sha256(video.read_bytes()).hexdigest(),before_hash),eq((folder/'upload-check-media/unit-01.mp4').read_bytes(),raw)))
 evidence['localUploads']=section(results[mark:],'HTTP PUT media; separate ignored local directory')
 evidence['executedAt']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());evidence['sourceCommitRole']='tested source commit; exact test inputs are identified by sourceHashes';evidence['sourceCommit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();evidence['sourceHashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['materials/business.json','materials/python_server.py','materials/acceptance.py','worker/domain.mjs','scripts/dev.mjs','scripts/local-sqlite.mjs','scripts/review-checks.py','web/app.js']}
 for k in ['boundaries','media','storage','snapshots']:
  script={'boundaries':'scripts/check-boundaries.mjs','media':'scripts/check-media.mjs','storage':'scripts/check-storage.mjs','snapshots':'scripts/verify-snapshots.py'}[k]
  if (ROOT/script).exists():
   p=subprocess.run([sys.executable if script.endswith('.py') else NODE,script],capture_output=True,text=True,check=True);evidence[k]=json.loads(p.stdout) if k in ['storage','snapshots'] else section([{'name':name,'status':'passed'} for name in p.stdout.strip().split(': ',1)[1].split(', ')], 'local module boundary checks')
 (ROOT/'content/evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
 failures=[r for run in evidence['runs'] for r in run['results'] if r['status']=='failed']+[r for r in results if r['status']=='failed']
 print(json.dumps({'runs':[(r['label'],r['passed'],r['failed']) for r in evidence['runs']],'checks':results,'failures':failures},ensure_ascii=False,indent=2));sys.exit(bool(failures))
finally:
 for p,log in children:
  p.terminate()
 for p,log in children:
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:p.kill();p.wait()
  log.close()
