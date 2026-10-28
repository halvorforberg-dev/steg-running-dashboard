import json, subprocess, time
from pathlib import Path
TARGETS=((1.0,'1 km',0.08),(5.0,'5 km',0.20))
DIST_KEYS=('distance','distanceMeters','totalDistance','splitDistance','lapDistance')
TIME_KEYS=('duration','elapsedDuration','movingDuration','totalDuration','timerTime')
def _number(d,keys):
 for k in keys:
  v=d.get(k)
  if isinstance(v,(int,float)) and not isinstance(v,bool):return float(v)
 return None
def _parts(node,path='root'):
 out=[]
 if isinstance(node,dict):
  low=path.lower()
  if 'split' in low or 'lap' in low:
   dist=_number(node,DIST_KEYS);secs=_number(node,TIME_KEYS)
   if dist is not None and secs is not None:
    km=dist/1000 if dist>100 else dist
    if secs>100000:secs/=1000
    out.append((km,secs,path))
  for k,v in node.items():out.extend(_parts(v,path+'.'+str(k)))
 elif isinstance(node,list):
  for i,v in enumerate(node):out.extend(_parts(v,path+'['+str(i)+']'))
 return out
def _best(existing,candidate):
 if not existing or candidate['seconds']<existing['seconds']:return candidate
 return existing
def activity_records(activities):
 best={}
 for a in activities:
  for target,label,tol in TARGETS:
   if abs(float(a['km'])-target)<=tol:
    c={'person':a['person'],'label':label,'distanceKm':target,'seconds':round(float(a['minutes'])*60),'date':a['date'],'activityId':a['id'].split(':',1)[-1],'title':a.get('title','Løpeøkt'),'source':'garmin_activity'}
    best[(a['person'],target)]=_best(best.get((a['person'],target)),c)
 return best
def enrich(cli,key,token,person,activities,previous,max_new=20):
 best={(r['person'],float(r['distanceKm'])):r for r in previous.get('records',[]) if r.get('person') and r.get('distanceKm') in (1,5)}
 for k,v in activity_records(activities).items():best[k]=_best(best.get(k),v)
 inspected=set(previous.get('inspected',{}).get(person,[]))
 # Fastest average pace first. Scan a bounded number of previously uninspected Garmin runs each cycle.
 candidates=sorted([a for a in activities if a['person']==person and float(a['km'])>=.95 and a['id'].split(':',1)[-1] not in inspected],key=lambda a:float(a['minutes'])/float(a['km']))[:max_new]
 for a in candidates:
  aid=a['id'].split(':',1)[-1]
  cmd=[str(cli),'--api-key-file',str(key),'--bearer-token-cache-file',str(token),'--timeout','30','--quiet','activity',aid]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
  if r.returncode:continue
  try:detail=json.loads(r.stdout)
  except Exception:continue
  for km,secs,path in _parts(detail):
   for target,label,tol in TARGETS:
    if abs(km-target)<=tol and ((target==1 and 120<=secs<=1200) or (target==5 and 600<=secs<=7200)):
     c={'person':person,'label':label,'distanceKm':target,'seconds':round(secs),'date':a['date'],'activityId':aid,'title':a.get('title','Løpeøkt'),'source':'garmin_split'}
     best[(person,target)]=_best(best.get((person,target)),c)
  inspected.add(aid);time.sleep(.05)
 old=previous.get('inspected',{});old[person]=sorted(inspected)
 return {'records':list(best.values()),'inspected':old}
