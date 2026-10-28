import getpass,os
from pathlib import Path
p=Path(__file__).resolve().parent/'.private';p.mkdir(exist_ok=True)
for n in ('Halvor','Tore','Kjetil'):
 v=getpass.getpass(n+' Garmin API-nøkkel (Enter beholder/utelater): ').strip()
 if v:(p/(n.lower()+'.key')).write_text(v,encoding='utf-8')
print('Nøkler lagret lokalt i .private.')
