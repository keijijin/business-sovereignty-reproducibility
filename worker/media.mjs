// Private, owner-scoped video storage. No public media URLs or access changes.
export async function handleMedia(request,bucket,owner){
 const path=new URL(request.url).pathname;
 if(!path.startsWith('/media/')&&!path.startsWith('/api/media'))return null;
 const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}});
 if(!owner)return json({error:'サインインしてください'},401);
 if(!bucket)return json({error:'動画ストレージが未接続です'},503);
 const prefix='owner/'+encodeURIComponent(owner)+'/videos/';
 if(path==='/api/media'&&request.method==='GET'){
  const units=await Promise.all(Array.from({length:8},async(_,i)=>{const unit=String(i+1).padStart(2,'0');const head=await bucket.head(prefix+unit+'.mp4');return {unit,available:!!head,size:head?.size||0};}));return json({units});
 }
 const match=path.match(/^\/(?:api\/media|media)\/(0[1-8])(?:\.mp4)?$/);
 if(!match)return json({error:'動画が見つかりません'},404);
 const key=prefix+match[1]+'.mp4';
 if(request.method==='PUT'&&path.startsWith('/api/media/')){
  const origin=request.headers.get('origin');if(origin&&origin!==new URL(request.url).origin)return json({error:'別サイトからの変更は拒否しました'},403);
  if(!request.headers.get('content-type')?.includes('video/mp4'))return json({error:'MP4動画を選択してください'},415);
  const length=Number(request.headers.get('content-length')||0);if(length>64000000)return json({error:'64MB以下の動画を選択してください'},413);
  const bytes=await request.arrayBuffer();if(bytes.byteLength<12||bytes.byteLength>64000000)return json({error:'動画のサイズが不正です'},400);
  if(new TextDecoder().decode(bytes.slice(4,8))!=='ftyp')return json({error:'MP4の形式が不正です'},400);
  await bucket.put(key,bytes,{httpMetadata:{contentType:'video/mp4'},customMetadata:{unit:match[1],source:'Notebook video overview'}});
  return json({unit:match[1],available:true,size:bytes.byteLength});
 }
 if(!['GET','HEAD'].includes(request.method)||!path.startsWith('/media/'))return json({error:'操作が未定義です'},405);
 const head=await bucket.head(key);if(!head)return json({error:'動画の配置が完了していません'},404);
 const total=head.size;let offset=0,end=total-1,status=200;
 const range=request.headers.get('range');
 if(range){const m=range.match(/^bytes=(\d*)-(\d*)$/);if(!m||(!m[1]&&!m[2]))return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+total}});
  if(!m[1])offset=Math.max(0,total-Number(m[2]));else{offset=Number(m[1]);if(m[2])end=Math.min(end,Number(m[2]));}
  if(offset>end||offset>=total)return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+total}});status=206;
 }
 const headers={'Content-Type':'video/mp4','Accept-Ranges':'bytes','Content-Length':String(end-offset+1),'Cache-Control':'private, max-age=300','X-Content-Type-Options':'nosniff',...(head.httpEtag?{ETag:head.httpEtag}:{})};
 if(status===206)headers['Content-Range']='bytes '+offset+'-'+end+'/'+total;
 if(request.method==='HEAD')return new Response(null,{status,headers});
 const object=await bucket.get(key,status===206?{range:{offset,length:end-offset+1}}:undefined);
 if(!object)return json({error:'動画が見つかりません'},404);
 return new Response(object.body,{status,headers});
}
