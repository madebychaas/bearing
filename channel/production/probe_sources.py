"""Read-only endpoint check; evidence is retained outside the published viewer."""
import concurrent.futures, json, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

URLS = {
 'NASA':'https://www.nasa.gov/feed/', 'NOAA':'https://www.noaa.gov/rss.xml',
 'NSF':'https://www.nsf.gov/rss/rss_www_news.xml',
 'NIST':'https://www.nist.gov/news-events/news/rss.xml',
 'Library of Congress':'https://www.loc.gov/rss/lcnews.xml',
 'NIH':'https://www.nih.gov/news-events/news-releases/rss.xml',
 'Federal Reserve':'https://www.federalreserve.gov/feeds/press_all.xml',
 'BLS':'https://www.bls.gov/feed/news_release/rss.xml',
 'USGS':'https://www.usgs.gov/news/all/feed',
 'BBC World':'https://feeds.bbci.co.uk/news/world/rss.xml',
 'BBC Technology':'https://feeds.bbci.co.uk/news/technology/rss.xml',
 'BBC Business':'https://feeds.bbci.co.uk/news/business/rss.xml',
 'BBC Health':'https://feeds.bbci.co.uk/news/health/rss.xml',
 'BBC Culture':'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
 'BBC Sport':'https://feeds.bbci.co.uk/sport/rss.xml',
 'NPR':'https://feeds.npr.org/1001/rss.xml',
 'PBS NewsHour':'https://www.pbs.org/newshour/feeds/rss/headlines',
 'The Guardian World':'https://www.theguardian.com/world/rss',
 'The Guardian Culture':'https://www.theguardian.com/culture/rss',
 'DW':'https://rss.dw.com/rdf/rss-en-world',
 'France 24':'https://www.france24.com/en/rss',
 'Al Jazeera':'https://www.aljazeera.com/xml/rss/all.xml',
 'Texas Tribune':'https://www.texastribune.org/feeds/latest/',
 'KERA':'https://www.keranews.org/news.rss',
}
def probe(pair):
 name,url=pair
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'BearingNewsPreview/1.0 (personal news reader)'})
  with urllib.request.urlopen(req,timeout=18) as response:
   body=response.read(2000001);result={'name':name,'url':url,'finalUrl':response.url,'http':response.status,'etag':response.headers.get('ETag'),'lastModified':response.headers.get('Last-Modified')}
  root=ET.fromstring(body)
  items=[n for n in root.iter() if n.tag.split('}')[-1] in ('item','entry')]
  def fields(item):
   return {n.tag.split('}')[-1]:(''.join(n.itertext()).strip() if n.tag.split('}')[-1]!='link' else n.attrib.get('href',n.text or ''))[:800] for n in item if n.tag.split('}')[-1] in ('title','link','pubDate','published','updated','date','description','summary')}
  result.update(root=root.tag,count=len(items),sample=[fields(i) for i in items[:2]],status='ok' if items else 'empty')
 except Exception as exc:result={'name':name,'url':url,'status':'unavailable','reason':str(exc)}
 return result
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(probe,URLS.items()))
 path=Path(__file__).parent/'runs'/'source-probe.json';path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps({'checkedAt':datetime.now(timezone.utc).isoformat(),'sources':results},indent=2),encoding='utf-8')
 for result in results:print(json.dumps({k:v for k,v in result.items() if k!='sample'}))
