import json,sys,re
d=json.load(open(sys.argv[1]))
KEEP_TAGS={'Hall of Fame','Repair Log','Portable','Medical','Limited Edition','Integrated Radio',"Kids' Character TV",'Integrated Game Console'}
def L(x,k): return x['raw'].get(k,[])
import re as _r
def P(x,k): return [v for v in L(x,k) if _r.search(r'\d',v)]
def yr(x):
    for v in L(x,'Launched'):
        m=re.search(r'(19|20)\d\d',v)
        if m: return int(m.group(0))
    return 0
out=[]
for x in d:
    if not x.get('size_in'): continue
    out.append([x['name'],x['brand'].strip(),x['series'],x['application'] or '',round(x['size_in'],1),x['aspect'],
      x['inputs'],x['mask'].replace('Monochrome Tube (no mask)','Monochrome'),x['tube_brand'],x['tube_model'],x['country'],
      x['weight_lbs'] or 0,x['url'].split('/crts/')[1],x['resolutions'],x['formats'],
      P(x,'Jungle IC'),L(x,'Chassis'),L(x,'Flyback'),L(x,'Yoke'),L(x,'Remote'),P(x,'Vertical Output IC'),L(x,'Mods'),
      yr(x),(L(x,'MSRP') or [''])[0],L(x,'Comb Filtering'),L(x,'Power Standard'),(L(x,'Market') or [''])[0],x['sync'],
      x.get('image',''),[t for t in x['tags'] if t in KEEP_TAGS],x['h_scan']])
out.sort(key=lambda r:(r[1].lower(),r[0].lower()))
js='const SETS='+json.dumps(out,separators=(',',':'),ensure_ascii=False)+';'
open('data.js','w',encoding='utf-8').write(js)
print(len(out),'sets',len(js)//1024,'KB',file=sys.stderr)
