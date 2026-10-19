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
# ---- twins: sets that share size plus 3+ of chassis/tube/flyback/yoke/jungle (incl. chassis or tube)
N=lambda s:re.sub(r'[^A-Z0-9]','',str(s).upper())
sig=[(r[4],{N(v) for v in r[16]},N(r[9]),{N(v) for v in r[17]},{N(v) for v in r[18]},{N(v) for v in r[15]}) for r in out]
par=list(range(len(out)))
def f(x):
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
for i in range(len(out)):
    a=sig[i]
    for j in range(i+1,len(out)):
        c=sig[j]
        if abs(a[0]-c[0])>0.5: continue
        ch=bool(a[1]&c[1]); tb=bool(a[2] and a[2]==c[2])
        if not(ch or tb): continue
        m=ch+tb+bool(a[3]&c[3])+bool(a[4]&c[4])+bool(a[5]&c[5])
        if m>=3: par[f(i)]=f(j)
groups={}
for i in range(len(out)): groups.setdefault(f(i),[]).append(i)
twins=[g for g in groups.values() if len(g)>1]
twins.sort(key=lambda g:(-len({out[i][1].lower() for i in g}),-len(g)))
print(len(twins),'twin groups',sum(map(len,twins)),'sets',file=sys.stderr)
js='const SETS='+json.dumps(out,separators=(',',':'),ensure_ascii=False)+';\nconst TWINS='+json.dumps(twins,separators=(',',':'))+';'
open('data.js','w',encoding='utf-8').write(js)
print(len(out),'sets',len(js)//1024,'KB',file=sys.stderr)
