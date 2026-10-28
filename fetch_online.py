import json,os,subprocess,sys
from pathlib import Path
import garmin_records
N=('Halvor','Tore','Kjetil')
def safe(e):
 s=str(e);return s if s in {'AUTH_401','ACCESS_403','RATE_429','GARMIN_REQUEST'} else type(e).__name__
def fetch(name,cli):
 secret=os.getenv('GARMIN_'+name.upper(),'').strip()
 if not secret:return [],{'status':'not_configured'},None,None
 key=Path('.'+name.lower()+'.key');token=Path('.'+name.lower()+'-token.json');key.write_text(secret,encoding='utf-8');rows=[]
 for pg in range(100):
  r=subprocess.run([str(cli),'--api-key-file',str(key),'--bearer-token-cache-file',str(token),'--quiet','activities','--start',str(pg*100),'--limit','100'],capture_output=True,text=True,timeout=90)
  if r.returncode:
   x=r.stderr.lower();raise RuntimeError('AUTH_401' if '401' in x else 'ACCESS_403' if '403' in x else 'RATE_429' if '429' in x else 'GARMIN_REQUEST')
  data=json.loads(r.stdout)
  for a in data:
   kind=a.get('activityType',{});kind=kind.get('typeKey','') if isinstance(kind,dict) else kind
   if 'running' not in str(kind).lower():continue
   km=float(a['distance'])/1000;mins=float(a['duration'])/60
   if km<=0 or mins<=0:continue
   rows.append({'id':name+':'+str(a['activityId']),'person':name,'date':str(a['startTimeLocal'])[:10],'title':str(a.get('activityName') or 'Løpeøkt')[:100],'km':km,'minutes':mins,'hr':a.get('averageHR') if isinstance(a.get('averageHR'),(int,float)) else None,'elevation':a.get('elevationGain') if isinstance(a.get('elevationGain'),(int,float)) else None})
  if len(data)<100:break
 rows=list({x['id']:x for x in rows}.values());return rows,{'status':'ok','count':len(rows)},key,token
def main():
 cli=Path(sys.executable).parent/('gc-personal.exe' if os.name=='nt' else 'gc-personal');old={}
 if Path('data.json').exists():
  try:
   d=json.loads(Path('data.json').read_text(encoding='utf-8'));old=d.get('recordScan',{'records':d.get('records',[]),'inspected':{}})
  except Exception:old={}
 old=old or {'records':[],'inspected':{}};acts=[];status={};keys=[]
 try:
  for n in N:
   r,s,k,t=fetch(n,cli);acts+=r;status[n]=s
   if k:keys.append((n,k,t))
  for n,k,t in keys:old=garmin_records.enrich(cli,k,t,n,acts,old)
  Path('data.json').write_text(json.dumps({'activities':acts,'sync':status,'records':old.get('records',[]),'recordScan':old},ensure_ascii=False),encoding='utf-8')
 finally:
  for _,k,t in keys:k.unlink(missing_ok=True);t.unlink(missing_ok=True)
if __name__=='__main__':main()
