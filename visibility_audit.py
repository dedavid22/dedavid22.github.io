"""Auditoria gratuita HTTP/HTML: no mide posiciones ni apariciones en IA."""
import argparse,datetime,json,pathlib,urllib.request,urllib.error,urllib.parse,xml.etree.ElementTree as ET
from html.parser import HTMLParser
SITES={"VecinosCanarios":"https://vecinoscanarios.onrender.com/","RMT Algo Lab":"https://rmt-algo-lab.pages.dev/","Apollo Servicios":"https://dedavid22.github.io/"}
class Doc(HTMLParser):
 def __init__(self):
  super().__init__();self.t=False;self.title=[];self.description=False;self.canonical=[];self.h1=0;self.lang="";self.jsonld=0;self.og=False;self.robots=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=="html":self.lang=a.get("lang","")
  if tag=="title":self.t=True
  if tag=="h1":self.h1+=1
  if tag=="meta":
   if a.get("name","").lower()=="description" and a.get("content","").strip():self.description=True
   if a.get("name","").lower()=="robots":self.robots.append(a.get("content",""))
   if a.get("property","").lower()=="og:title":self.og=True
  if tag=="link" and "canonical" in a.get("rel","").lower():self.canonical.append(a.get("href",""))
  if tag=="script" and a.get("type","").lower()=="application/ld+json":self.jsonld+=1
 def handle_endtag(self,tag):
  if tag=="title":self.t=False
 def handle_data(self,txt):
  if self.t:self.title.append(txt)
def get(url):
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"ApolloVisibilityAudit/1.0"})
  with urllib.request.urlopen(req,timeout=18) as r:return r.status,r.read(1300000).decode(r.headers.get_content_charset() or "utf-8","replace"),None
 except urllib.error.HTTPError as e:return e.code,"",None
 except Exception as e:return None,"",str(e)
def audit(name,url):
 base=urllib.parse.urlsplit(url);origin=base.scheme+"://"+base.netloc
 home,body,err=get(url);rob,robot,err2=get(origin+"/robots.txt");smap,xml,err3=get(origin+"/sitemap.xml");llms,_,err4=get(origin+"/llms.txt")
 h=Doc()
 if home==200:
  try:h.feed(body)
  except Exception:pass
 can=h.canonical[0] if h.canonical else ""
 checks={"home_http_200":home==200,"title":bool("".join(h.title).strip()),"meta_description":h.description,"h1_present":h.h1>0,"canonical_origin":bool(can and urllib.parse.urlsplit(urllib.parse.urljoin(url,can)).netloc==base.netloc),"html_lang":bool(h.lang),"open_graph_title":h.og,"json_ld":h.jsonld>0,"no_noindex":not any("noindex" in x.lower() for x in h.robots),"robots_200":rob==200,"sitemap_in_robots":rob==200 and "sitemap:" in robot.lower(),"sitemap_200":smap==200}
 urls=[]
 if smap==200:
  try:
   tree=ET.fromstring(xml);urls=[el.text for el in tree.iter() if el.tag.endswith("}loc") and el.text][:500]
  except ET.ParseError:pass
 checks["sitemap_valid"]=len(urls)>0
 return {"site":name,"url":url,"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"checks":checks,"passed":sum(checks.values()),"total":len(checks),"sitemap_urls":len(urls),"sample_sitemap_urls":urls[:5],"llms_optional_http":llms,"errors":[e for e in [err,err2,err3,err4] if e]}
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",default="audit_results");a=p.parse_args()
 path=pathlib.Path(a.out);path.mkdir(parents=True,exist_ok=True)
 data=[audit(n,u) for n,u in SITES.items()]
 (path/"report.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
 lines=["# Auditoria SEO/AEO de tus webs","Comprobaciones tecnicas, no prueban aparecer en respuestas IA, ranking ni indexacion.","","| Sitio | Controles | URLs sitemap | llms.txt opcional |","|---|---:|---:|---|"]
 for x in data:lines.append("| %s | %d/%d | %d | %s |"%(x["site"],x["passed"],x["total"],x["sitemap_urls"],x["llms_optional_http"]))
 for x in data:
  lines.extend(["","## "+x["site"],x["url"],""])
  for k,v in x["checks"].items():lines.append(("- [x] " if v else "- [ ] ")+k)
 (path/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps([{"site":x["site"],"passed":x["passed"],"total":x["total"],"sitemap_urls":x["sitemap_urls"]} for x in data],ensure_ascii=False))
if __name__=="__main__":main()
