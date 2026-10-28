import base64,hmac,json,os,subprocess,sys,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
BASE=Path(__file__).resolve().parent;PRIVATE=BASE/'.private';N=('Halvor','Tore','Kjetil');CACHE={'activities':[],'sync':{}};LOCK=threading.Lock()
def safe(e):
 s=str(e);return s if s in {'AUTH_401','ACCESS_403','RATE_429','GARMIN_REQUEST'} else type(e).__name__
def fetch(name):
 key=PRIVATE/(name.lower()+'.key')
 if not key.exists():return [],{'status':'not_configured'}
 cli=Path(sys.executable).parent/('gc-personal.exe' if os.name=='nt' else 'gc-personal');rows=[]
 for pg in range(100):
  r=subprocess.run([str(cli),'--api-key-file',str(key),'--bearer-token-cache-file',str(PRIVATE/(name.lower()+'-token.json')),'--quiet','activities','--start',str(pg*100),'--limit','100'],capture_output=True,text=True,timeout=90)
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
 rows=list({x['id']:x for x in rows}.values());return rows,{'status':'ok','count':len(rows)}
def sync():
 global CACHE
 while True:
  acts=[];status={}
  for n in N:
   try:r,s=fetch(n);acts+=r;status[n]=s
   except Exception as e:status[n]={'status':'error','reason':safe(e)}
  if not any(s.get('status')=='error' for s in status.values()):
   with LOCK:CACHE={'activities':acts,'sync':status};(BASE/'data.json').write_text(json.dumps(CACHE,ensure_ascii=False),encoding='utf-8')
  time.sleep(3600)
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  route=self.path.split('?',1)[0]
  if route in ('/','/STEG.html'):p=BASE/'STEG.html';mime='text/html; charset=utf-8'
  elif route in ('/data.json','/api/dashboard'):p=BASE/'data.json';mime='application/json; charset=utf-8'
  else:self.send_error(404);return
  b=p.read_bytes();self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
def main():
 threading.Thread(target=sync,daemon=True).start();print('Åpne http://127.0.0.1:8787');ThreadingHTTPServer(('127.0.0.1',8787),H).serve_forever()
if __name__=='__main__':main()
