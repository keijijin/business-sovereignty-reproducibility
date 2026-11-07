#!/usr/bin/env python3
"""Check retained evidence, paired references, and rendered manuscript geometry.
This checks identity and document structure; it is not a semantic proof.
"""
import hashlib,json,re
from pathlib import Path
import pdfplumber
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
evidence=json.loads((ROOT/'content/evidence.json').read_text());refs=json.loads((HERE/'references.json').read_text())
assert len(refs)==17 and [r['number'] for r in refs]==list(range(1,18))
assert evidence['sourceCommit']=='130054398f6c72c071fdeea266fcac714250fd1f'
for p,h in evidence['sourceHashes'].items():assert sha(ROOT/p)==h,p
assert [(r['passed'],r['failed']) for r in evidence['runs']]==[(44,0),(44,0)]
for k,n in {'migration':6,'regressions':6,'specConfiguration':4,'storage':5,'boundaries':4,'media':7,'localUploads':1,'snapshots':18}.items():assert evidence[k]['passed']==n and evidence[k]['failed']==0,k
observations={}
for lang in ['en','ja']:
 text=(HERE/f'paper-{lang}.md').read_text();assert 'REFERENCES_PLACEHOLDER' not in text
 reference_numbers=[int(x) for x in re.findall(r'^\[(\d+)\]',text,re.M)];assert reference_numbers==list(range(1,18))
 assert '130054398f6c72c071fdeea266fcac714250fd1f' in text and '233e9e46592ba48b5686dae99c7c829edb31e09c' in text
 assert all(x in text for x in ['44','200','120','2,000','1,048,576','1,169,346'])
 reader=PdfReader(HERE/f'paper-{lang}.pdf');extracted='\n'.join(p.extract_text() for p in reader.pages)
 assert ('Keiji Jin' if lang=='en' else '神') in extracted and '44' in extracted and '[16]' in extracted
 bounds=[]
 with pdfplumber.open(HERE/f'paper-{lang}.pdf') as pdf:
  for i,p in enumerate(pdf.pages,1):
   assert p.chars and all(-.1<=c['x0']<=c['x1']<=p.width+.1 and -.1<=c['top']<=c['bottom']<=p.height+.1 for c in p.chars),f'{lang} page {i} overflow'
   body=[c for c in p.chars if 50<c['top']<740];assert max(c['bottom'] for c in body)<735,f'{lang} page {i} footer collision'
   bounds.append({'page':i,'body_right_pt':round(max(c['x1'] for c in body),2),'body_bottom_pt':round(max(c['bottom'] for c in body),2)})
 fonts={str(v.get_object().get('/BaseFont')) for p in reader.pages for v in p['/Resources']['/Font'].values()}
 if lang=='ja':assert any('HiraMin' in f for f in fonts),'Japanese font missing'
 observations[lang]={'pages':len(reader.pages),'reference_count':17,'author_present':True,'glyph_bounds':'within page; separated from footer','fonts':sorted(fonts),'page_bounds':bounds}
claims={
 'public_artifact':{'url':'https://github.com/keijijin/business-sovereignty-reproducibility','fixed_tag':'artifact-v1.0.0','history':'fresh sanitized export; development commits are historical provenance'},
 'study_kind':'constructed technical case and retrospective artifact analysis; not independent replication or controlled AI comparison',
 'acceptance':{'source':'content/evidence.json#runs','passed_per_realization':44,'failed_per_realization':0,'independent_samples':False},
 'small_migration':{'source':'content/evidence.json#migration; scripts/review-checks.py','directions':2,'fixtures_per_direction':1,'assertions_total':6,'directly_compared':['requests','policyHistory'],'not_independently_asserted':'all top-level export fields'},
 'capacity':{'source':'content/evidence.json#regressions; scripts/review-checks.py','records_per_source':200,'title_code_points':120,'reason_code_points':2000,'export_threshold_bytes':1048576,'exact_export_bytes_recorded':False,'assertions_total':6,'maximum_history_workload':False},
 'configuration':{'source':'content/evidence.json#specConfiguration','assertions':4,'scope':'selected field/part settings and unsupported state rejection, not arbitrary prose-to-code'},
 'storage':{'source':'content/evidence.json#storage','checks':5,'environment':'actual local SQLite, not comprehensive hosted D1'},
 'historical_counterexamples':{'source':'user-supplied review and docs/review-remediation.md','reproduced_for_manuscript':False,'reported_old_checks_per_realization':21,'reported_failing_state_bytes':1169346,'reported_failing_records':90},
 'hosted':{'source':'docs/hosted-review-verification.md','source_commit':'8ef0f63b71cbbad26feb7f2d797f825d3203e50d','scope':'existing approved request retained; policy v2 to v1 to v2 with actor/time audit; evidence presentation','full_suite_through_hosted_identity':False},
 'not_established':['complete equivalence','autonomous regeneration','AI-provider exchange','cost or performance superiority','organizational sovereignty','historical inevitability'],
 'source_hashes':evidence['sourceHashes']}
(HERE/'claim-evidence.json').write_text(json.dumps(claims,ensure_ascii=False,indent=2)+'\n')
files=['paper-en.md','paper-ja.md','paper-en.docx','paper-ja.docx','paper-en.pdf','paper-ja.pdf','references.json','references.bib','build_documents.py','validate_paper.py','claim-evidence.json','README.md']
result={'validated_on':'2026-11-07','tested_code_baseline':evidence['sourceCommit'],'artifact_snapshot':'233e9e46592ba48b5686dae99c7c829edb31e09c','validation_scope':'source identity, result counts, reference numbering, paired version/number sanity, PDF geometry and embedded CJK font; not semantic equivalence proof','new_api_test_run_for_manuscript':False,'visual_review':'Final publication-update pages rendered and inspected; embedded Japanese font retained.','documents':observations,'sha256':{name:sha(HERE/name) for name in files}}
(HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','reference_count':17,'pages':{k:v['pages'] for k,v in observations.items()},'source_hashes_match':True},ensure_ascii=False))
