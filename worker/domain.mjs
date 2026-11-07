export class Fault extends Error { constructor(status,message){super(message);this.status=status;} }
let config,actors,parts,limits,fields,trimChars;
const fail=(status,message)=>{throw new Fault(status,message)};
export function configureSpec(spec){
 if(!spec||spec.id!=='BS-CR'||!spec.contractVersion||!Array.isArray(spec.states)||spec.states.join(',')!=='draft,submitted,approved,rejected,withdrawn')throw Error('Unsupported business specification states');
 for(const name of ['records','bodyBytes','workspaceBytes','recordBytes','historyEvents','policyEvents'])if(!Number.isSafeInteger(spec.limits?.[name])||spec.limits[name]<1)throw Error('Invalid spec limit: '+name);
 for(const name of ['title','reason'])if(!Number.isSafeInteger(spec.fields?.[name])||spec.fields[name]<1)throw Error('Invalid spec field: '+name);
 if(!Array.isArray(spec.parts)||!spec.parts.length||!spec.parts.every(x=>typeof x==='string')||!spec.actors||!spec.administration?.tenant||!Array.isArray(spec.wire?.trimCodePoints)||!Array.isArray(spec.progress?.units)||!Array.isArray(spec.progress?.answerValues))throw Error('Incomplete business specification');
 for(const a of Object.values(spec.actors))if(typeof a.tenant!=='string'||!Array.isArray(a.roles)||!a.roles.length||!a.roles.every(r=>['designer','approver'].includes(r)))throw Error('Invalid spec actor');
 if(!Object.values(spec.actors).some(a=>a.tenant===spec.administration.tenant&&a.roles.includes(spec.administration.role))||![1,2].includes(spec.defaults?.policyVersion))throw Error('Invalid administration/default specification');
 config=structuredClone(spec);({actors,parts,limits,fields}=config);trimChars=new Set(config.wire.trimCodePoints.map(c=>String.fromCodePoint(c)));
}
const trim=s=>{const a=Array.from(s);while(a.length&&trimChars.has(a[0]))a.shift();while(a.length&&trimChars.has(a.at(-1)))a.pop();return a.join('')};
const text=(s,max)=>typeof s==='string'&&!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(s)&&Array.from(s).length<=max&&trim(s).length>0;
const integer=n=>Number.isSafeInteger(n)&&n>=0;
const policy=n=>integer(n)&&[1,2].includes(n);
const bytes=x=>new TextEncoder().encode(JSON.stringify(x)).length;
const iso=s=>typeof s==='string'&&!s.startsWith('0000')&&/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString()===s;
const admin=a=>a.tenant===config.administration.tenant&&a.roles.includes(config.administration.role);
const attrs=r=>({title:r.title,part:r.part,reason:r.reason});
const attributes=r=>r&&text(r.title,fields.title)&&text(r.reason,fields.reason)&&parts.includes(r.part);
export const initial=()=>{if(!config)throw Error('Specification must be configured before startup');return {revision:0,policyVersion:config.defaults.policyVersion,requests:[],policyHistory:[]}};
function policyHistory(events,version){
 if(!Array.isArray(events)||events.length>limits.policyEvents)fail(400,'仕様監査が不正です');let prior;
 for(const e of events){if(!e||e.action!=='policy-change'||!actors[e.actor]||!admin(actors[e.actor])||!iso(e.at)||!policy(e.from)||!policy(e.to)||(prior&&prior.to!==e.from)||(prior&&prior.at>e.at))fail(400,'仕様監査の役割・日時・連続性が不正です');prior=e;}
 if(prior&&prior.to!==version)fail(400,'仕様版と監査が一致しません');return structuredClone(events);
}
function validatePack(pack){
 if(!pack||pack.format!=='business-sovereignty/1'||!policy(pack.policyVersion)||!Array.isArray(pack.requests)||pack.requests.length>limits.records)fail(400,'移行パックの形式が不正です');const ids=new Set();
 for(const r of pack.requests){
  if(!r||typeof r.id!=='string'||!/^cr-[a-f0-9-]{36}$/.test(r.id)||ids.has(r.id)||!actors[r.createdBy]||!actors[r.createdBy].roles.includes('designer')||actors[r.createdBy].tenant!==r.tenant||!attributes(r)||!config.states.includes(r.status)||!Array.isArray(r.history)||!r.history.length||r.history.length>limits.historyEvents||bytes(r)>limits.recordBytes)fail(400,'申請・起票役割・参照・履歴が不正です');
  ids.add(r.id);let previous=null,priorAt,tracked;
  for(let i=0;i<r.history.length;i++){
   const h=r.history[i],person=actors[h?.actor];if(!h||!person||person.tenant!==r.tenant||!iso(h.at)||!policy(h.policyVersion)||h.from!==previous||(priorAt&&priorAt>h.at))fail(400,'監査履歴の連続性が不正です');
   if(i===0){if(h.action!=='create'||h.to!=='draft'||h.actor!==r.createdBy||!person.roles.includes('designer'))fail(400,'起票履歴が不正です');if(h.after){if(!attributes(h.after))fail(400,'起票属性が不正です');tracked=attrs(h.after)}}
   else if(['submit','edit','withdraw'].includes(h.action)){
    const to={submit:'submitted',edit:'draft',withdraw:'withdrawn'}[h.action];if(h.from!=='draft'||h.to!==to||h.actor!==r.createdBy||!person.roles.includes('designer'))fail(400,'設計者の操作履歴が不正です');
    if(h.action==='edit'){if(!attributes(h.before)||!attributes(h.after)||(tracked&&JSON.stringify(tracked)!==JSON.stringify(attrs(h.before))))fail(400,'訂正の前後が不正です');tracked=attrs(h.after)}
   }else if(['approve','reject'].includes(h.action)){
    if(h.from!=='submitted'||h.to!==(h.action==='approve'?'approved':'rejected')||!person.roles.includes('approver')||(h.policyVersion===2&&h.actor===r.createdBy)||(h.action==='reject'&&!text(h.reason,fields.reason)))fail(400,'承認履歴が不正です');
   }else fail(400,'未定義の監査操作です');previous=h.to;priorAt=h.at;
  }
  if(previous!==r.status||r.createdAt!==r.history[0].at||(tracked&&JSON.stringify(tracked)!==JSON.stringify(attrs(r))))fail(400,'属性・状態と履歴が一致しません');
 }
 return {requests:structuredClone(pack.requests),policyHistory:policyHistory(pack.policyHistory||[],pack.policyVersion)};
}
export async function handleApi(request,repo,owner){
 const json=(v,status=200)=>Response.json(v,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
 try{
  if(!config)throw Error('Specification not configured');if(!owner)fail(401,'サインインしてください');const actorId=request.headers.get('x-demo-actor')||'aya',actor=actors[actorId];if(!actor)fail(403,'実験人物が未定義です');
  const path=new URL(request.url).pathname,method=request.method;const stored=await repo.load(owner),s=stored?structuredClone(stored):initial();s.policyHistory??=[];
  if(method==='GET'){
   if(path==='/api/state'){const learning=await repo.loadProgress(owner)||{revision:0,entries:s.progress||{}};return json({...s,progress:learning.entries,progressRevision:learning.revision,policyHistory:admin(actor)?s.policyHistory:[],requests:s.requests.filter(r=>r.tenant===actor.tenant),actor:{id:actorId,...actor},parts,workspaceScope:'authenticated-owner / demo personas'});}
   if(path==='/api/export'){if(!admin(actor))fail(403,'workspace全体のexportには管理テナントの承認者が必要です');return json({format:'business-sovereignty/1',contractVersion:config.contractVersion,policyVersion:s.policyVersion,policyHistory:s.policyHistory,requests:s.requests,exportedAt:new Date().toISOString(),scope:config.administration.exportScope});}
   const m=path.match(/^\/api\/requests\/(cr-[a-f0-9-]{36})$/);if(m){const r=s.requests.find(r=>r.id===m[1]&&r.tenant===actor.tenant);if(!r)fail(404,'申請が見つかりません');return json({request:r,revision:s.revision})}fail(404,'APIが見つかりません');
  }
  if(method!=='POST')fail(405,'この操作はPOSTです');const origin=request.headers.get('origin');if(origin&&origin!==new URL(request.url).origin)fail(403,'別サイトからの変更は拒否しました');
  if(!request.headers.get('content-type')?.includes('application/json'))fail(415,'JSONで送信してください');const raw=await request.text();if(new TextEncoder().encode(raw).length>limits.bodyBytes)fail(413,'入力が大きすぎます');let body;try{body=JSON.parse(raw)}catch{fail(400,'JSONの形式が不正です')};if(!body||typeof body!=='object'||Array.isArray(body))fail(400,'入力はオブジェクトです');const now=new Date().toISOString();
  if(path==='/api/progress'){
   if(!config.progress.units.includes(body.unit)||!integer(body.answer)||!config.progress.answerValues.includes(body.answer))fail(400,'単元と回答が不正です');const learning=await repo.loadProgress(owner)||{revision:0,entries:s.progress||{}};
   if(!integer(body.progressRevision)||body.progressRevision!==learning.revision)fail(409,'学習記録を再読み込みしてください');learning.entries[body.unit]={answer:body.answer,at:now};const old=learning.revision;learning.revision++;if(!await repo.saveProgress(owner,learning,old))fail(409,'学習の同時更新を検出しました');return json({progressRevision:learning.revision,revision:s.revision});
  }
  if(!integer(body.revision)||body.revision!==s.revision)fail(409,'別の更新がありました。再読み込みしてください');let result={};
  const history=(r,action,to,extra={})=>{r.history.push({action,actor:actorId,at:now,from:r.status,to,policyVersion:s.policyVersion,...extra});r.status=to;};
  if(path==='/api/requests'){
   if(!actor.roles.includes('designer'))fail(403,'起票には設計者の役割が必要です');if(!attributes(body))fail(400,'タイトル・部品・変更理由を正しく入力してください');if(s.requests.length>=limits.records)fail(409,'申請件数の上限です。exportしてください');
   const r={id:'cr-'+crypto.randomUUID(),title:trim(body.title),part:body.part,reason:trim(body.reason),tenant:actor.tenant,createdBy:actorId,createdAt:now,status:null,history:[]};history(r,'create','draft',{after:attrs(r)});s.requests.unshift(r);result={request:r};
  }else if(path==='/api/policy'){
   if(!admin(actor))fail(403,'仕様切替には管理テナントの承認者が必要です');if(!policy(body.version))fail(400,'仕様版は1か2です');if(s.policyHistory.length>=limits.policyEvents)fail(413,'仕様監査の保存上限です');s.policyHistory.push({action:'policy-change',actor:actorId,at:now,from:s.policyVersion,to:body.version});s.policyVersion=body.version;
  }else if(path==='/api/import'){
   if(!admin(actor))fail(403,'importには管理テナントの承認者が必要です');if(s.requests.length||s.policyHistory.length)fail(409,'空の業務ワークスペースにのみimportできます');const v=validatePack(body.pack);s.requests=v.requests;s.policyHistory=v.policyHistory;s.policyVersion=body.pack.policyVersion;result={imported:s.requests.length};
  }else{
   const m=path.match(/^\/api\/requests\/(cr-[a-f0-9-]{36})(?:\/(submit|approve|reject|withdraw))?$/);if(!m)fail(404,'操作が見つかりません');const r=s.requests.find(x=>x.id===m[1]&&x.tenant===actor.tenant);if(!r)fail(404,'申請が見つかりません');const action=m[2]||'edit';
   if(['submit','edit','withdraw'].includes(action)){
    if(actorId!==r.createdBy||!actor.roles.includes('designer'))fail(403,'起票者だけが操作できます');if(r.status!=='draft')fail(409,'draft以外は訂正・提出・取下げできません');
    if(action==='edit'){if(!attributes(body))fail(400,'訂正内容が不正です');if(r.history.length>=limits.historyEvents-2)fail(413,'提出と判断の監査枠を確保するため訂正を拒否しました');const before=attrs(r);r.title=trim(body.title);r.reason=trim(body.reason);r.part=body.part;history(r,'edit','draft',{before,after:attrs(r)});}else history(r,action,action==='submit'?'submitted':'withdrawn');
   }else{
    if(!actor.roles.includes('approver'))fail(403,'承認者の役割が必要です');if(r.status!=='submitted')fail(409,'submittedだけを承認・却下できます');if(s.policyVersion===2&&actorId===r.createdBy)fail(403,'R04：仕様v2では自己承認・自己却下を禁止します');if(action==='reject'&&!text(body.reason,fields.reason))fail(400,'却下理由を入力してください');history(r,action,action==='approve'?'approved':'rejected',action==='reject'?{reason:trim(body.reason)}:{});
   }result={request:r};
  }
  for(const r of s.requests)if(r.history.length>limits.historyEvents||bytes(r)>limits.recordBytes)fail(413,'申請または監査の保存上限です');const oldRevision=s.revision;s.revision++;if(bytes(s)>limits.workspaceBytes)fail(413,'workspace保存サイズの上限です');if(!await repo.save(owner,s,oldRevision))fail(409,'同時更新を検出しました。再読み込みしてください');return json({...result,revision:s.revision},path==='/api/requests'?201:200);
 }catch(e){return json({error:e instanceof Fault?e.message:'サーバーで処理に失敗しました'},e instanceof Fault?e.status:500)}
}
export function d1Repository(db){return {
 async load(id){const out=await db.prepare("SELECT w.body AS metadata,c.body AS piece FROM workspaces w LEFT JOIN workspace_chunks c ON c.owner=w.id AND c.token=json_extract(w.body,'$.chunkToken') WHERE w.id=? ORDER BY c.seq").bind(id).all();const rows=out.results;if(!rows.length)return null;const meta=JSON.parse(rows[0].metadata);if(!meta.chunkToken)return meta;if(rows.length!==meta.chunks||rows.some(r=>r.piece===null))throw Error('Incomplete workspace storage');return JSON.parse(rows.map(r=>r.piece).join(''));},
 async save(id,s,revision){const token=crypto.randomUUID(),body=JSON.stringify(s),pieces=[];for(let at=0;at<body.length;){let end=Math.min(at+50000,body.length);if(end<body.length&&/[\uD800-\uDBFF]/.test(body[end-1]))end--;pieces.push(body.slice(at,end));at=end;}const metadata=JSON.stringify({chunkToken:token,chunks:pieces.length});
  const change=revision===0?db.prepare('INSERT INTO workspaces(id,revision,body) VALUES(?,?,?) ON CONFLICT(id) DO NOTHING').bind(id,s.revision,metadata):db.prepare('UPDATE workspaces SET revision=?,body=? WHERE id=? AND revision=?').bind(s.revision,metadata,id,revision);
  const statements=[change,...pieces.map((piece,seq)=>db.prepare('INSERT INTO workspace_chunks(owner,token,seq,body) SELECT ?,?,?,? WHERE EXISTS(SELECT 1 FROM workspaces WHERE id=? AND body=?)').bind(id,token,seq,piece,id,metadata)),db.prepare('DELETE FROM workspace_chunks WHERE owner=? AND token!=? AND EXISTS(SELECT 1 FROM workspaces WHERE id=? AND body=?)').bind(id,token,id,metadata)];const result=await db.batch(statements);return result[0].meta.changes===1;},
 async loadProgress(id){const row=await db.prepare('SELECT body FROM learning_progress WHERE id=?').bind(id).first();return row?JSON.parse(row.body):null;},
 async saveProgress(id,p,revision){const out=revision===0?await db.prepare('INSERT INTO learning_progress(id,revision,body) VALUES(?,?,?) ON CONFLICT(id) DO NOTHING').bind(id,p.revision,JSON.stringify(p)).run():await db.prepare('UPDATE learning_progress SET revision=?,body=? WHERE id=? AND revision=?').bind(p.revision,JSON.stringify(p),id,revision).run();return out.meta.changes===1;}
}}
