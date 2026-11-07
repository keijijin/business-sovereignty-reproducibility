#!/usr/bin/env python3
"""Independent specification-configured Python/SQLite realization. Loopback only."""
import argparse,copy,json,re,sqlite3,uuid
from datetime import datetime,timezone
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
class Fault(Exception):
 def __init__(self,status,msg):self.status=status;super().__init__(msg)
def need(ok,status,msg):
 if not ok:raise Fault(status,msg)
def number(s):
 f=float(s);return int(f) if f.is_integer() and abs(f)<=9007199254740991 else f
def reject_constant(name):raise ValueError('non-standard JSON constant '+name)
def loads(raw):return json.loads(raw,parse_float=number,parse_constant=reject_constant)
def integer(n):return type(n) in (int,float) and 0<=n<=9007199254740991 and n%1==0
def policy(n):return integer(n) and n in (1,2)
def size(v):return len(json.dumps(v,ensure_ascii=False,separators=(',',':')).encode())
def configure(spec):
 global SPEC,ACTORS,PARTS,LIMITS,FIELDS,TRIM
 if spec.get('id')!='BS-CR' or not spec.get('contractVersion') or spec.get('states')!=['draft','submitted','approved','rejected','withdrawn']:raise ValueError('Unsupported business specification states')
 for key in ['records','bodyBytes','workspaceBytes','recordBytes','historyEvents','policyEvents']:
  if not integer(spec.get('limits',{}).get(key)) or spec['limits'][key]<1:raise ValueError('Invalid spec limit: '+key)
 for key in ['title','reason']:
  if not integer(spec.get('fields',{}).get(key)) or spec['fields'][key]<1:raise ValueError('Invalid spec field: '+key)
 if not spec.get('parts') or not all(isinstance(p,str) for p in spec['parts']) or not spec.get('actors') or not spec.get('administration',{}).get('tenant') or not isinstance(spec.get('wire',{}).get('trimCodePoints'),list) or not isinstance(spec.get('progress',{}).get('units'),list) or not isinstance(spec.get('progress',{}).get('answerValues'),list):raise ValueError('Incomplete business specification')
 for a in spec['actors'].values():
  if not isinstance(a.get('tenant'),str) or not a.get('roles') or not all(r in ['designer','approver'] for r in a['roles']):raise ValueError('Invalid spec actor')
 if not any(a['tenant']==spec['administration']['tenant'] and spec['administration']['role'] in a['roles'] for a in spec['actors'].values()) or not policy(spec.get('defaults',{}).get('policyVersion')):raise ValueError('Invalid administration/default specification')
 SPEC=copy.deepcopy(spec);ACTORS=SPEC['actors'];PARTS=SPEC['parts'];LIMITS=SPEC['limits'];FIELDS=SPEC['fields'];TRIM=''.join(chr(c) for c in SPEC['wire']['trimCodePoints'])
def text(v,n):return isinstance(v,str) and not any(0xd800<=ord(c)<=0xdfff for c in v) and len(v)<=n and bool(v.strip(TRIM))
def attrs(r):return {k:r[k] for k in ['title','part','reason']}
def attributes(r):return isinstance(r,dict) and text(r.get('title'),FIELDS['title']) and text(r.get('reason'),FIELDS['reason']) and r.get('part') in PARTS
def admin(a):return a['tenant']==SPEC['administration']['tenant'] and SPEC['administration']['role'] in a['roles']
def iso(s):
 if not isinstance(s,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z',s):return False
 try:return datetime.fromisoformat(s.replace('Z','+00:00')).isoformat(timespec='milliseconds').replace('+00:00','Z')==s
 except ValueError:return False
def initial():return {'revision':0,'policyVersion':SPEC['defaults']['policyVersion'],'requests':[],'policyHistory':[]}
def validate(pack):
 need(isinstance(pack,dict) and pack.get('format')=='business-sovereignty/1' and policy(pack.get('policyVersion')) and isinstance(pack.get('requests'),list) and len(pack['requests'])<=LIMITS['records'],400,'移行形式が不正です')
 ids=set()
 for r in pack['requests']:
  need(isinstance(r,dict),400,'申請が不正です');creator=ACTORS.get(r.get('createdBy'),{})
  need(isinstance(r.get('id'),str) and re.fullmatch(r'cr-[a-f0-9-]{36}',r['id']) and r['id'] not in ids and 'designer' in creator.get('roles',[]) and creator.get('tenant')==r.get('tenant') and attributes(r) and r.get('status') in SPEC['states'] and isinstance(r.get('history'),list) and 1<=len(r['history'])<=LIMITS['historyEvents'],400,'申請・起票役割・参照が不正です')
  need(size(r)<=LIMITS['recordBytes'],400,'申請が大きすぎます');ids.add(r['id']);previous=None;prior_at=None;tracked=None
  for i,h in enumerate(r['history']):
   need(isinstance(h,dict),400,'監査が不正です');person=ACTORS.get(h.get('actor'),{})
   need(person.get('tenant')==r['tenant'] and iso(h.get('at')) and policy(h.get('policyVersion')) and h.get('from')==previous and (prior_at is None or prior_at<=h['at']),400,'監査の連続性が不正です')
   if i==0:
    need(h.get('action')=='create' and h.get('to')=='draft' and h.get('actor')==r['createdBy'] and 'designer' in person.get('roles',[]),400,'起票履歴が不正です')
    if h.get('after') is not None:need(attributes(h['after']),400,'起票属性が不正です');tracked=attrs(h['after'])
   elif h.get('action') in ['submit','edit','withdraw']:
    action=h['action'];to={'submit':'submitted','edit':'draft','withdraw':'withdrawn'}[action]
    need(h.get('from')=='draft' and h.get('to')==to and h.get('actor')==r['createdBy'] and 'designer' in person.get('roles',[]),400,'設計者の操作履歴が不正です')
    if action=='edit':
     need(attributes(h.get('before')) and attributes(h.get('after')) and (tracked is None or tracked==attrs(h['before'])),400,'訂正前後が不正です');tracked=attrs(h['after'])
   elif h.get('action') in ['approve','reject']:
    action=h['action'];need(h.get('from')=='submitted' and h.get('to')==('approved' if action=='approve' else 'rejected') and 'approver' in person.get('roles',[]) and (h['policyVersion']==1 or h['actor']!=r['createdBy']) and (action!='reject' or text(h.get('reason'),FIELDS['reason'])),400,'承認履歴が不正です')
   else:raise Fault(400,'未定義の操作です')
   previous=h['to'];prior_at=h['at']
  need(previous==r['status'] and r.get('createdAt')==r['history'][0]['at'] and (tracked is None or tracked==attrs(r)),400,'属性・最終状態と履歴が不正です')
 events=pack.get('policyHistory',[]);need(isinstance(events,list) and len(events)<=LIMITS['policyEvents'],400,'仕様監査が不正です');prior=None
 for e in events:
  need(isinstance(e,dict) and e.get('action')=='policy-change' and e.get('actor') in ACTORS and admin(ACTORS[e['actor']]) and iso(e.get('at')) and policy(e.get('from')) and policy(e.get('to')) and (prior is None or prior['to']==e['from'] and prior['at']<=e['at']),400,'仕様監査の役割・日時・連続性が不正です');prior=e
 need(prior is None or prior['to']==pack['policyVersion'],400,'仕様版と監査が一致しません')
 return copy.deepcopy(pack['requests']),copy.deepcopy(events)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def respond(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
 def do_GET(self):self.run_action(False)
 def do_POST(self):self.run_action(True)
 def do_PUT(self):self.respond(405,{'error':'この操作はPOSTです'})
 def run_action(self,write):
  conn=sqlite3.connect(DB)
  try:
   aid=self.headers.get('X-Demo-Actor') or 'aya';need(aid in ACTORS,403,'実験人物が不正です');a=ACTORS[aid]
   if write:conn.execute('BEGIN IMMEDIATE')
   row=conn.execute('SELECT body FROM workspace WHERE id=1').fetchone();s=json.loads(row[0]) if row else initial();s.setdefault('policyHistory',[]);path=self.path.split('?')[0]
   def learning():
    row=conn.execute('SELECT body FROM learning_progress WHERE id=1').fetchone();return json.loads(row[0]) if row else {'revision':0,'entries':s.get('progress',{})}
   if not write:
    if path=='/api/state':
     p=learning();self.respond(200,{**s,'progress':p['entries'],'progressRevision':p['revision'],'policyHistory':s['policyHistory'] if admin(a) else [],'requests':[r for r in s['requests'] if r['tenant']==a['tenant']],'actor':{'id':aid,**a},'parts':PARTS,'workspaceScope':'authenticated-owner / demo personas'});return
    if path=='/api/export':
     need(admin(a),403,'workspace全体のexportには管理テナントの承認者が必要です');self.respond(200,{'format':'business-sovereignty/1','contractVersion':SPEC['contractVersion'],'policyVersion':s['policyVersion'],'policyHistory':s['policyHistory'],'requests':s['requests'],'exportedAt':datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'),'scope':SPEC['administration']['exportScope']});return
    m=re.fullmatch(r'/api/requests/(cr-[a-f0-9-]{36})',path)
    if m:
     r=next((r for r in s['requests'] if r['id']==m[1] and r['tenant']==a['tenant']),None);need(r,404,'申請がありません');self.respond(200,{'request':r,'revision':s['revision']});return
    raise Fault(404,'APIがありません')
   origin=self.headers.get('Origin');need(not origin or origin=='http://'+self.headers.get('Host'),403,'別サイトからの更新です');need('application/json' in self.headers.get('Content-Type',''),415,'JSONで送信してください')
   try:length=int(self.headers.get('Content-Length',0))
   except ValueError:raise Fault(400,'Content-Lengthが不正です')
   need(0<=length<=LIMITS['bodyBytes'],413,'入力が大きすぎます')
   try:b=loads(self.rfile.read(length))
   except Exception:raise Fault(400,'JSONが不正です')
   need(isinstance(b,dict),400,'オブジェクトが必要です');now=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z');out={}
   if path=='/api/progress':
    need(b.get('unit') in SPEC['progress']['units'] and integer(b.get('answer')) and b['answer'] in SPEC['progress']['answerValues'],400,'単元と回答が不正です');p=learning();need(integer(b.get('progressRevision')) and b['progressRevision']==p['revision'],409,'学習の同時更新です');p['entries'][b['unit']]={'answer':b['answer'],'at':now};p['revision']+=1;conn.execute('INSERT INTO learning_progress VALUES(1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(json.dumps(p,ensure_ascii=False),));conn.commit();self.respond(200,{'progressRevision':p['revision'],'revision':s['revision']});return
   need(integer(b.get('revision')) and b['revision']==s['revision'],409,'同時更新を検出しました')
   def event(r,action,to,extra=None):
    h={'action':action,'actor':aid,'at':now,'from':r['status'],'to':to,'policyVersion':s['policyVersion']};h.update(extra or {});r['history'].append(h);r['status']=to
   if path=='/api/requests':
    need('designer' in a['roles'],403,'設計者の役割が必要です');need(attributes(b),400,'入力が不正です');need(len(s['requests'])<LIMITS['records'],409,'申請件数の上限です')
    r={'id':'cr-'+str(uuid.uuid4()),'title':b['title'].strip(TRIM),'part':b['part'],'reason':b['reason'].strip(TRIM),'tenant':a['tenant'],'createdBy':aid,'createdAt':now,'status':None,'history':[]};event(r,'create','draft',{'after':attrs(r)});s['requests'].insert(0,r);out={'request':r}
   elif path=='/api/policy':
    need(admin(a),403,'管理テナントの承認者が必要です');need(policy(b.get('version')),400,'仕様版が不正です');need(len(s['policyHistory'])<LIMITS['policyEvents'],413,'仕様監査の保存上限です');s['policyHistory'].append({'action':'policy-change','actor':aid,'at':now,'from':s['policyVersion'],'to':b['version']});s['policyVersion']=b['version']
   elif path=='/api/import':
    need(admin(a),403,'管理テナントの承認者が必要です');need(not s['requests'] and not s['policyHistory'],409,'空の移行先にのみimportできます');s['requests'],s['policyHistory']=validate(b.get('pack'));s['policyVersion']=b['pack']['policyVersion'];out={'imported':len(s['requests'])}
   else:
    m=re.fullmatch(r'/api/requests/(cr-[a-f0-9-]{36})(?:/(submit|approve|reject|withdraw))?',path);need(m,404,'操作がありません');r=next((r for r in s['requests'] if r['id']==m[1] and r['tenant']==a['tenant']),None);need(r,404,'申請がありません');action=m[2] or 'edit'
    if action in ['submit','edit','withdraw']:
     need(aid==r['createdBy'] and 'designer' in a['roles'],403,'起票者だけが操作できます');need(r['status']=='draft',409,'draft以外は訂正・提出・取下げできません')
     if action=='edit':
      need(attributes(b),400,'訂正内容が不正です');need(len(r['history'])<LIMITS['historyEvents']-2,413,'提出と判断の監査枠を確保するため訂正を拒否しました');before=attrs(r);r.update({'title':b['title'].strip(TRIM),'part':b['part'],'reason':b['reason'].strip(TRIM)});event(r,'edit','draft',{'before':before,'after':attrs(r)})
     else:event(r,action,'submitted' if action=='submit' else 'withdrawn')
    else:
     need('approver' in a['roles'],403,'承認者が必要です');need(r['status']=='submitted',409,'submittedだけを承認・却下できます');need(s['policyVersion']==1 or aid!=r['createdBy'],403,'v2では自己承認を禁止します')
     if action=='reject':need(text(b.get('reason'),FIELDS['reason']),400,'却下理由が必要です')
     event(r,action,'approved' if action=='approve' else 'rejected',{'reason':b['reason'].strip(TRIM)} if action=='reject' else None)
    out={'request':r}
   need(all(len(r['history'])<=LIMITS['historyEvents'] and size(r)<=LIMITS['recordBytes'] for r in s['requests']),413,'申請または監査の保存上限です');s['revision']+=1;need(size(s)<=LIMITS['workspaceBytes'],413,'workspace保存サイズの上限です');conn.execute('INSERT INTO workspace VALUES(1,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',(json.dumps(s,ensure_ascii=False,separators=(',',':')),));conn.commit();self.respond(201 if path=='/api/requests' else 200,{**out,'revision':s['revision']})
  except Fault as e:conn.rollback();self.respond(e.status,{'error':str(e)})
  except Exception:conn.rollback();self.respond(500,{'error':'サーバー処理に失敗しました'})
  finally:conn.close()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('port',type=int,nargs='?',default=4178);parser.add_argument('database',nargs='?',default='sovereignty-python.sqlite');parser.add_argument('--spec',type=Path,default=Path(__file__).with_name('business.json'));args=parser.parse_args();configure(json.loads(args.spec.read_text()));DB=Path(args.database);DB.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(DB) as conn:
  conn.execute('CREATE TABLE IF NOT EXISTS workspace(id INTEGER PRIMARY KEY CHECK(id=1),body TEXT)');conn.execute('CREATE TABLE IF NOT EXISTS learning_progress(id INTEGER PRIMARY KEY CHECK(id=1),body TEXT)')
 print(f'Python realization: http://127.0.0.1:{args.port}',flush=True);HTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
