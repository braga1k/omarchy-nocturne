#!/usr/bin/env python3
"""Read-only reproduction of published medians from counter samples."""
from pathlib import Path
import gzip,json,statistics as st
ROOT=Path(__file__).resolve().parents[1]
data=json.loads(gzip.decompress((ROOT/'docs/performance/samples.json.gz').read_bytes()))
result={'shell':{},'morph':{}}
for variant in ['stock','nocturne','optimized']:
 trials=[t for t in data['shell'] if t['variant']==variant]
 if not trials:continue
 rows=[]
 for t in trials:
  phases={}
  for phase in ['idle','menu','audio']:
   a=[x for x in t['samples'] if x['phase']==phase];dt=a[-1]['t']-a[0]['t']
   phases[phase]={k:{'cpu_pct_one_core':100*(a[-1][k]['cpu_s']-a[0][k]['cpu_s'])/dt,'children_cpu_pct':100*(a[-1][k]['children_cpu_s']-a[0][k]['children_cpu_s'])/dt,'pss_mib':st.median(x[k]['Pss_kib']/1024 for x in a)} for k in ['shell','compositor']}
  rows.append(phases)
 result['shell'][variant]={p:{process:{metric:{'median':st.median(r[p][process][metric] for r in rows),'min':min(r[p][process][metric] for r in rows),'max':max(r[p][process][metric] for r in rows)} for metric in ['cpu_pct_one_core','children_cpu_pct','pss_mib']} for process in ['shell','compositor']} for p in ['idle','menu','audio']}
for variant in ['before','after']:
 rows=[]
 for t in data['morph']:
  if t['variant']!=variant:continue
  a=t['samples'];e=t['launches'];assert all('moving' in event['phases'] for event in e)
  peaks=[max(x['gpu_fb_mib'] or 0 for x in a if event['t']<=x['t']<=event['t']+1.5) for event in e]
  rows.append({'cpu_ms_per_cycle':1000*(a[-1]['shell']['cpu_s']-a[0]['shell']['cpu_s'])/len(e),'pss_mib_max':max(x['shell']['Pss_kib']/1024 for x in a),'gpu_fb_mib_typical_peak':st.median(peaks),'gpu_fb_mib_run_max':max(x['gpu_fb_mib'] or 0 for x in a),'gpu_fb_mib_after_idle':st.median(x['gpu_fb_mib'] for x in a if x['phase']=='post-idle')})
 result['morph'][variant]={k:{'median':st.median(x[k] for x in rows),'min':min(x[k] for x in rows),'max':max(x[k] for x in rows)} for k in rows[0]}
print(json.dumps(result,indent=2))
