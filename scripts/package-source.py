from pathlib import Path
import zipfile
root=Path('.');out=root/'outputs'/'business-sovereignty-source.zip';out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(root.rglob('*')):
  if p.is_file() and not any(x in {'.git','.local','dist','outputs','media','snapshots','__pycache__'} for x in p.parts) and not p.name.startswith('.env'):
   z.write(p,p.as_posix())
print(out)
