"""Cross-realization migration and rejection, through HTTP only."""
import json,sys,urllib.request,urllib.error,copy,time
source,target=sys.argv[1:3]
def api(base,path,body=None,actor='kai'):
 req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','X-Demo-Actor':actor},method='POST' if body is not None else 'GET')
 try:
  with urllib.request.urlopen(req) as r:return r.status,json.load(r)
 except urllib.error.HTTPError as e:return e.code,json.load(e)
def s(base,actor='kai'):return api(base,'/api/state',actor=actor)[1]
checks=[]
def ok(name,condition):
 checks.append({'name':name,'status':'passed' if condition else 'failed'});assert condition,name
rev=s(source)['revision'];_,out=api(source,'/api/requests',{'revision':rev,'title':'実装を越える設計変更','part':'SNS-002 温度センサー 改訂B','reason':'同一IDと履歴で業務を継承する'})
rid=out['request']['id'];api(source,f'/api/requests/{rid}/submit',{'revision':s(source)['revision']})
pack=api(source,'/api/export')[1];before=s(target);bad=copy.deepcopy(pack);bad['requests'][0]['history'][-1]['to']='approved'
status,_=api(target,'/api/import',{'pack':bad,'revision':before['revision']})
ok('不正な履歴を400で拒否し空の移行先を保持',status==400 and s(target)==before)
status,res=api(target,'/api/import',{'pack':pack,'revision':before['revision']})
ok('JavaScriptのexportをPythonへimport',status==200 and res['imported']==len(pack['requests']))
imported=api(target,'/api/export')[1]
ok('ID・属性・状態・監査履歴の完全一致',imported['requests']==pack['requests'])
status,_=api(target,f'/api/requests/{rid}/approve',{'revision':s(target,'ren')['revision']},'ren')
r=next(r for r in s(target)['requests'] if r['id']==rid)
old=next(r for r in pack['requests'] if r['id']==rid)
ok('同じIDの申請を別承認者で継続し承認',status==200 and r['status']=='approved' and r['history'][:-1]==old['history'])
status,_=api(target,f'/api/requests/{rid}/approve',{'revision':s(target,'mio')['revision']},'mio')
ok('移行後もテナント境界を維持',status==404)
print(json.dumps({'status':'passed','executedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'description':'JavaScriptからPythonへ移行。不正パック拒否、ID・状態・履歴の一致、別承認者による処理続行、テナント分離をHTTPで確認。','source':source,'target':target,'records':len(pack['requests']),'results':checks},ensure_ascii=False,indent=2))
