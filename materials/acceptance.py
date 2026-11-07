"""Black-box HTTP acceptance, extended with review counterexamples; not blind."""
import json, sys, urllib.request, urllib.error, time
from pathlib import Path

base=sys.argv[1].rstrip('/')
results=[]
def call(path, method='GET', data=None, actor='kai'):
    req=urllib.request.Request(base+path, data=None if data is None else json.dumps(data).encode(), method=method,headers={'Content-Type':'application/json','X-Demo-Actor':actor})
    started=time.perf_counter()
    try:
        with urllib.request.urlopen(req) as r: out=(r.status,json.load(r))
    except urllib.error.HTTPError as r: out=(r.code,json.load(r))
    return out
def check(name, fn):
    try: fn(); results.append({'name':name,'status':'passed'})
    except Exception as e: results.append({'name':name,'status':'failed','error':str(e)})
def eq(a,b): assert a==b, f'{a!r} != {b!r}'
def state(actor='kai'): return call('/api/state',actor=actor)[1]
def create(actor='kai',**kw):
    return call('/api/requests','POST',{'title':'熱変形への対応','part':'BRK-001 ブラケット 改訂A','reason':'高温時の寸法安定性を改善する','revision':state(actor)['revision'],**kw},actor)
def act(id,action,actor='kai',**kw): return call('/api/requests/'+id+'/'+action,'POST',{'revision':state(actor)['revision'],**kw},actor)
def policy(version): return call('/api/policy','POST',{'version':version,'revision':state()['revision']})

# A malformed pack must be rejected while the destination is empty.
import copy,uuid
sample={'id':'cr-'+str(uuid.uuid4()),'title':'😀'*120,'part':'BRK-001 ブラケット 改訂A','reason':'理由','tenant':'atelier','createdBy':'aya','createdAt':'2026-11-06T00:00:00.000Z','status':'draft','history':[{'action':'create','actor':'aya','at':'2026-11-06T00:00:00.000Z','from':None,'to':'draft','policyVersion':2}]}
def invalid_pack(name,mutate):
 p={'format':'business-sovereignty/1','policyVersion':2,'requests':[copy.deepcopy(sample)]};mutate(p);before=state();eq(call('/api/import','POST',{'revision':before['revision'],'pack':p})[0],400);eq(state(),before)
check('交換契約: 非ISO日時の拒否',lambda:invalid_pack('date',lambda p:(p['requests'][0].update(createdAt='11/06/2026'),p['requests'][0]['history'][0].update(at='11/06/2026'))))
check('交換契約: 年0000の拒否',lambda:invalid_pack('date',lambda p:p['requests'][0]['history'][0].update(at='0000-01-01T00:00:00.000Z')))
check('交換契約: 存在しない暦日の拒否',lambda:invalid_pack('date',lambda p:p['requests'][0]['history'][0].update(at='2026-02-30T00:00:00.000Z')))
check('交換契約: 起票役割のない履歴を拒否',lambda:invalid_pack('role',lambda p:(p['requests'][0].update(createdBy='ren'),p['requests'][0]['history'][0].update(actor='ren'))))
check('交換契約: 真偽値の仕様版を拒否',lambda:invalid_pack('version',lambda p:p.update(policyVersion=True)))
check('交換契約: 不正サロゲートを拒否',lambda:eq(create(title='\ud800')[0],400))
check('交換契約: 絵文字120文字を受理',lambda:eq(create(title='😀'*120)[0],201))
check('交換契約: 絵文字121文字を拒否',lambda:eq(create(title='😀'*121)[0],400))
for invalid in [True,1.5,'1',None]:check('交換契約: 非整数revision '+repr(invalid),lambda invalid=invalid:eq(create(revision=invalid)[0],409))
check('R06 別テナントのexportを拒否',lambda:eq(call('/api/export',actor='mio')[0],403))
check('R06 別テナントの仕様切替を拒否',lambda:eq(call('/api/policy','POST',{'version':1,'revision':state('mio')['revision']},'mio')[0],403))
check('学習保存は業務revisionを変更しない',lambda:(eq(call('/api/progress','POST',{'unit':'01','answer':0,'progressRevision':state()['progressRevision']})[0],200),eq(state()['revision'],1)))
_,draft=create();did=draft['request']['id']
check('R02 下書きを訂正',lambda:eq(call('/api/requests/'+did,'POST',{'revision':state()['revision'],'title':'訂正後','part':sample['part'],'reason':'理由の訂正'})[0],200))
check('R02 訂正前後を履歴に保存',lambda:eq(state()['requests'][0]['history'][-1]['before']['title'],'熱変形への対応'))
check('R02 下書きを取り下げ',lambda:eq(act(did,'withdraw')[0],200))
before=state()
check('R02 取下げ後の訂正を拒否',lambda:eq(call('/api/requests/'+did,'POST',{'revision':before['revision'],'title':'再訂正','part':sample['part'],'reason':'理由'})[0],409))
check('R02 拒否した訂正は本文と履歴を変えない',lambda:eq(state(),before))
check('R10 未知の実験人物を拒否',lambda:eq(call('/api/state',actor='unknown')[0],403))
check('R01 空白タイトルを拒否',lambda:eq(create(title='  ')[0],400))
check('R01 未定義部品を拒否',lambda:eq(create(part='imaginary')[0],400))
status,created=create(); rid=created.get('request',{}).get('id','missing')
check('R01 正常起票と初期状態',lambda:(eq(status,201),eq(created['request']['status'],'draft')))
check('R03 設計者による承認を拒否',lambda:eq(act(rid,'approve',actor='aya')[0],403))
check('R02 他人による提出を拒否',lambda:eq(act(rid,'submit',actor='aya')[0],403))
check('R02 起票者が提出',lambda:eq(act(rid,'submit')[0],200))
snapshot=state()
check('R04 v2で自己承認を拒否',lambda:eq(act(rid,'approve')[0],403))
check('R05 拒否時にデータと履歴を維持',lambda:eq(state(),snapshot))
check('R06 他テナントからIDを指定しても不可',lambda:eq(act(rid,'approve',actor='mio')[0],404))
check('R06 他テナント一覧に混入しない',lambda:eq(len(state('mio')['requests']),0))
check('R03 別承認者が承認',lambda:eq(act(rid,'approve',actor='ren')[0],200))
check('R02 承認済みの再提出を拒否',lambda:eq(act(rid,'submit')[0],409))
check('R07 3操作の監査と仕様版',lambda:(eq(len(state()['requests'][0]['history']),3),eq(state()['requests'][0]['history'][-1]['policyVersion'],2)))
check('R08 古いrevisionの更新を拒否',lambda:eq(create(revision=0)[0],409))
check('R04 v1へ切替',lambda:eq(policy(1)[0],200))
_,r=create(); id2=r['request']['id']; act(id2,'submit')
check('R04 v1で自己承認が可能',lambda:eq(act(id2,'approve')[0],200))
old=[x for x in state()['requests'] if x['id']==id2][0]
policy(2)
check('R04 仕様変更で過去履歴を改変しない',lambda:eq([x for x in state()['requests'] if x['id']==id2][0],old))
_,r=create(actor='aya'); id3=r['request']['id']; act(id3,'submit',actor='aya')
check('R05 理由なし却下を拒否',lambda:eq(act(id3,'reject',actor='ren',reason=' ')[0],400))
check('R05 理由付き却下',lambda:eq(act(id3,'reject',actor='ren',reason='熱試験の結果が必要')[0],200))
check('R09 非空移行先へのimportを拒否',lambda:eq(call('/api/import','POST',{'pack':call('/api/export')[1],'revision':state()['revision']})[0],409))
check('R04 真偽値の仕様切替を拒否',lambda:eq(policy(True)[0],400))
check('R07 仕様切替の操作者と時刻を保持',lambda:(eq(len(state()['policyHistory']),2),eq(state()['policyHistory'][0]['actor'],'kai'),eq(state()['policyHistory'][0]['from'],2),eq(state()['policyHistory'][1]['to'],2)))
check('交換契約: 数値として整数のrevision 1.0表現を受理',lambda:eq(create(revision=float(state()['revision']))[0],201))
out={'base':base,'executedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'kind':'local HTTP acceptance; not blind holdout','passed':sum(x['status']=='passed' for x in results),'failed':sum(x['status']=='failed' for x in results),'results':results}
print(json.dumps(out,ensure_ascii=False,indent=2))
sys.exit(bool(out['failed']))
