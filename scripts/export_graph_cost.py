"""Export a completed 384-query native graph profile: pass its run-directory name."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
label=sys.argv[1];p=root/'runs'/label
report=json.loads((p/'run.json').read_text());assert report['status']=='complete'
queries=json.loads((p/'queries.json').read_text())['queries'];assert len(queries)==384
for v in report['resources'].values():v.pop('cgroup',None)
report['plugins']=[Path(p['path']).name for p in report['plugins']]
report['queriesSha256']=hashlib.sha256((p/'queries.json').read_bytes()).hexdigest()
report['limitations']=['Fixed 32 public statement types, three repeats, not proof coverage or held-out evaluation.','Deterministic injected directions: zero model calls; Jev request latency is excluded.','Immutable graph shared; structural query caches independent from fixed warmup.','No-expansion should preserve the CPU base exactly; other ranking changes do not establish quality gains.','Full initialization is reported separately from queries.','Memory peaks are cumulative within the recorded cgroup; serial profiles can share a scope.']
public=[]
for row in queries:
 names=row['suggestions'];r={k:v for k,v in row.items() if k!='suggestions'}
 r['suggestionsSha256']=hashlib.sha256(json.dumps(names,separators=(',',':'),ensure_ascii=False).encode()).hexdigest();public.append(r)
pub=root/'docs'/f'{label}-queries.jsonl';pub.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in public))
report['publicQueries']={'path':pub.name,'sha256':hashlib.sha256(pub.read_bytes()).hexdigest()}
report['repeatStability']={}
for mode in ['base','none','forward','backward']:
 grouped={}
 for row in queries:
  if row['mode']==mode:grouped.setdefault(row['name'],[]).append(row['suggestions'])
 assert len(grouped)==32 and all(len(rows)==3 for rows in grouped.values())
 report['repeatStability'][mode]={'groups':32,'unstableGroups':sum(any(r!=rows[0] for r in rows[1:]) for rows in grouped.values())}
(root/'docs'/f'{label}.json').write_text(json.dumps(report,indent=2)+'\n')
print(label,'published with',len(queries),'rows')
