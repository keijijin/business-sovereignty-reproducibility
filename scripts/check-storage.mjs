import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {openLocalDatabase} from './local-sqlite.mjs';
import {configureSpec,handleApi,d1Repository} from '../worker/domain.mjs';
const spec=JSON.parse(readFileSync('materials/business.json'));configureSpec(spec);
const folder=mkdtempSync(join(tmpdir(),'bs-storage-')),path=join(folder,'test.sqlite');let db=openLocalDatabase(path),repo=d1Repository(db);
const request=b=>new Request('https://example.test/api/requests',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Actor':'kai'},body:JSON.stringify(b)});
try{
 const b={revision:0,title:'競合',reason:'確認',part:spec.parts[0]};
 const statuses=await Promise.all([handleApi(request(b),repo,'A'),handleApi(request(b),repo,'A')]).then(rs=>rs.map(r=>r.status).sort());assert.deepEqual(statuses,[201,409]);
 const first=await repo.load('A');assert.equal(first.requests.length,1);
 const huge={...first,revision:2,padding:'😀'.repeat(400000)};assert.equal(await repo.save('A',huge,1),true);assert.deepEqual(await repo.load('A'),huge);
 assert.equal(await repo.save('A',{...huge,revision:2,padding:'loser'},1),false);assert.deepEqual(await repo.load('A'),huge);
 db.close();db=openLocalDatabase(path);repo=d1Repository(db);assert.deepEqual(await repo.load('A'),huge);
 assert.equal(await repo.load('B'),null);
 console.log(JSON.stringify({kind:'real SQLite repository SQL, chunk transaction and restart',passed:5,failed:0,results:['CAS concurrent writer succeeds once','chunked >1MiB roundtrip','CAS loser preserves all chunks','restart persistence','owner isolation'].map(name=>({name,status:'passed'}))}));
}finally{db.close();rmSync(folder,{recursive:true,force:true});}
