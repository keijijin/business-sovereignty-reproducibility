import http from 'node:http';
import {mkdirSync,readFileSync,existsSync,writeFileSync,statSync} from 'node:fs';
import {resolve} from 'node:path';
import {handleMedia} from '../worker/media.mjs';
import {handleApi,configureSpec,d1Repository} from '../worker/domain.mjs';
import {openLocalDatabase} from './local-sqlite.mjs';
const spec=JSON.parse(readFileSync(process.env.BUSINESS_SPEC||'materials/business.json','utf8'));configureSpec(spec);
const uploadRoot=resolve(process.env.LOCAL_MEDIA_DIR||'.local/media');
const unit=key=>key.match(/videos\/(0[1-8])\.mp4$/)[1];
const uploaded=key=>resolve(uploadRoot,'unit-'+unit(key)+'.mp4');
const videoPath=key=>existsSync(uploaded(key))?uploaded(key):resolve('media/unit-'+unit(key)+'.mp4');
const bucket={head:async key=>{const p=videoPath(key);return existsSync(p)?{size:statSync(p).size}:null},get:async(key,opt)=>{let b=readFileSync(videoPath(key));if(opt?.range)b=b.subarray(opt.range.offset,opt.range.offset+opt.range.length);return {body:b}},put:async(key,bytes)=>{mkdirSync(uploadRoot,{recursive:true});writeFileSync(uploaded(key),Buffer.from(bytes));return {size:bytes.byteLength}}};
const port=Number(process.argv[2]||4177),db=resolve(process.argv[3]||'.local/dev.sqlite'),database=openLocalDatabase(db),repo=d1Repository(database);
const server=http.createServer(async(req,res)=>{
 try{const pathname=new URL(req.url,'http://127.0.0.1:'+port).pathname,max=pathname.startsWith('/api/media/')?64000000:spec.limits.bodyBytes;const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size<=max)chunks.push(chunk)}if(size>max){res.writeHead(413,{'Content-Type':'application/json'});res.end(JSON.stringify({error:'入力が大きすぎます'}));return}
 const body=Buffer.concat(chunks),headers={...req.headers,'oai-authenticated-user-id':'local-developer'};
 const request=new Request('http://127.0.0.1:'+port+req.url,{method:req.method,headers,...(body.length?{body}:{})});
 const isDomain=pathname.startsWith('/api/')&&!['/api/spec','/api/evidence','/api/lessons'].includes(pathname),mediaResponse=await handleMedia(request,bucket,'local-developer');
 const worker=(await import('../dist/server/index.js?build='+statSync('dist/server/index.js').mtimeMs)).default;
 const out=mediaResponse||(isDomain?await handleApi(request,repo,'local-developer'):pathname==='/api/spec'?Response.json(spec):await worker.fetch(request,{},{}));res.writeHead(out.status,Object.fromEntries(out.headers));res.end(Buffer.from(await out.arrayBuffer()));
 }catch(e){res.writeHead(500,{'Content-Type':'application/json'});res.end(JSON.stringify({error:e.message}));}
}).listen(port,'127.0.0.1',()=>console.log('Local: http://127.0.0.1:'+port));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>server.close(()=>{database.close();process.exit(0)}));
