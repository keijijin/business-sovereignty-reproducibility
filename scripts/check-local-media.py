import urllib.request,json
from pathlib import Path
base='http://127.0.0.1:4177'
results=[]
for n in range(1,9):
 unit=f'{n:02}';p=Path('media')/f'unit-{unit}.mp4'
 req=urllib.request.Request(base+f'/media/{unit}.mp4',method='HEAD')
 with urllib.request.urlopen(req) as r:assert r.status==200 and int(r.headers['Content-Length'])==p.stat().st_size
 req=urllib.request.Request(base+f'/media/{unit}.mp4',headers={'Range':'bytes=4-7'})
 with urllib.request.urlopen(req) as r:assert r.status==206 and r.read()==b'ftyp'
 results.append({'unit':unit,'status':'passed','checks':['actual MP4 content length','byte range seeking']})
print(json.dumps({'passed':8,'failed':0,'scope':'local HTTP video delivery','results':results},indent=2))
