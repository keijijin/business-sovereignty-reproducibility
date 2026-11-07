import {DatabaseSync} from 'node:sqlite';
import {readFileSync,mkdirSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
export function openLocalDatabase(filename){
 mkdirSync(dirname(resolve(filename)),{recursive:true});
 const db=new DatabaseSync(filename);db.exec('PRAGMA busy_timeout=5000');
 for(const file of ['0000_workspace.sql','0001_learning_and_chunks.sql']) db.exec(readFileSync(new URL('../drizzle/'+file,import.meta.url),'utf8').replaceAll('CREATE TABLE ','CREATE TABLE IF NOT EXISTS '));
 return {
  close:()=>db.close(),
  prepare(sql){return {bind(...args){return {
   first(){return db.prepare(sql).get(...args)||null;},
   all(){return {results:db.prepare(sql).all(...args)};},
   run(){return {meta:{changes:Number(db.prepare(sql).run(...args).changes)}};}
  };}};},
  batch(statements){
   db.exec('BEGIN IMMEDIATE');
   try{const results=statements.map(s=>s.run());db.exec('COMMIT');return results;}
   catch(e){db.exec('ROLLBACK');throw e;}
  }
 };
}
