# Recipe executed in the root tool call that produced sequence218.json.
from pathlib import Path
import subprocess,sys,json
f=Path('.factory/sequence218');f.mkdir(exist_ok=True)
rows=[]
for code in (0,7):
 log=f/f'consumer-{code}';p=subprocess.Popen([sys.executable,'-c',f'import time;time.sleep(.2);raise SystemExit({code})'])
 pending=p.poll() is None
 result=p.wait()
 if result==0:log.write_text('consumer after successful exit')
 assert pending and log.exists()==(code==0)
 rows.append({'producer_pending_observed':pending,'exit':result,'consumer_executed':log.exists()})
real=f/'real';sample=f/'sample';real.mkdir(exist_ok=True);sample.mkdir(exist_ok=True)
(real/'data').write_text('preserve');(sample/'data').write_text('reset sample')
assert (real/'data').read_text()=='preserve'
Path('.factory/sequence218.json').write_text(json.dumps({'sequence':rows,'separate_data_roots':True}))
print(rows)
