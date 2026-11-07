import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,cpSync,existsSync} from 'node:fs';
const read=p=>readFileSync(p,'utf8');
const assets={};for(const p of ['index.html','style.css','app.js'])assets['/'+(p==='index.html'?'':p)]=read('web/'+p);
for(let i=1;i<=8;i++){const n=String(i).padStart(2,'0');assets['/materials/unit-'+n+'.md']=read('content/unit-'+n+'.md');}
assets['/materials/business.json']=read('materials/business.json');
assets['/materials/methodology.md']=read('materials/methodology.md');
assets['/materials/acceptance.py']=read('materials/acceptance.py');
if(existsSync('materials/python_server.py'))assets['/materials/python_server.py']=read('materials/python_server.py');
assets['/materials/runbook.md']=read('materials/runbook.md');
assets['/materials/implementation-js.mjs']=read('worker/domain.mjs');
execFileSync('python3',['scripts/package-source.py']);
const sourceZip=readFileSync('outputs/business-sovereignty-source.zip').toString('base64');
const spec=JSON.parse(assets['/materials/business.json']);const lessons=JSON.parse(read('content/lessons.json'));
const evidence=existsSync('content/evidence.json')?JSON.parse(read('content/evidence.json')):{status:'未実行',runs:[]};
const domain=read('worker/domain.mjs').replaceAll('export ','');
const media=read('worker/media.mjs').replaceAll('export ','');
const main=`\nconfigureSpec(SPEC);\nexport default {async fetch(request,env){const url=new URL(request.url);const p=url.pathname;const common={'X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin'};
 const mediaResponse=await handleMedia(request,env.BUCKET,request.headers.get('oai-authenticated-user-id'));if(mediaResponse)return mediaResponse;
 if(p==='/materials/source.zip')return new Response(Uint8Array.from(atob(SOURCE_ZIP),c=>c.charCodeAt(0)),{headers:{'Content-Type':'application/zip','Content-Disposition':'attachment; filename=business-sovereignty-source.zip','X-Content-Type-Options':'nosniff'}});
 if(p==='/api/spec')return Response.json(SPEC);if(p==='/api/lessons')return Response.json(LESSONS);if(p==='/api/evidence')return Response.json(EVIDENCE,{headers:{'Cache-Control':'no-store'}});
 if(p.startsWith('/api/')){if(!env.DB)return Response.json({error:'データベースが未接続です'},{status:503});return handleApi(request,d1Repository(env.DB),request.headers.get('oai-authenticated-user-id'));}
 if(ASSETS[p]!==undefined){const type=p.endsWith('.css')?'text/css':p.endsWith('.js')?'text/javascript':p.endsWith('.json')?'application/json':p.endsWith('.md')||p.endsWith('.py')?'text/plain':'text/html';return new Response(ASSETS[p],{headers:{...common,'Content-Type':type+'; charset=utf-8',...(p.startsWith('/materials/')?{'Content-Disposition':'attachment; filename="'+p.split('/').pop()+'"'}:{}),'Content-Security-Policy':"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'self' https://chatgpt.com https://*.chatgpt.com"}})}
 return new Response('Not found',{status:404});}};`;
mkdirSync('dist/server',{recursive:true});mkdirSync('dist/.openai',{recursive:true});
writeFileSync('dist/server/index.js','const SOURCE_ZIP='+JSON.stringify(sourceZip)+';\nconst SPEC='+JSON.stringify(spec)+';\nconst LESSONS='+JSON.stringify(lessons)+';\nconst EVIDENCE='+JSON.stringify(evidence)+';\nconst ASSETS='+JSON.stringify(assets)+';\n'+domain+media+main);
cpSync('.openai/hosting.json','dist/.openai/hosting.json');console.log('Built standalone Worker + '+Object.keys(assets).length+' embedded assets');
