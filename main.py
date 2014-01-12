import os
import webapp2
import cgi
import json
import jinja2
import urllib2
import re
from google.appengine.ext import db
import wiki
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

params=dict()
params.clear()

# Api keys
CB_API_KEY="Enter Crunchbase Api key here"
GMAP_API_KEY="Enter Gmaps Api key here"
YouTube_API_KEY="Enter Youtube Api key here"


#duck duck go
def topic_summary(w):
    k=str(w)
    params["Keyword"]=k
    l=k.lower()
    t=l.replace (" ", "+")        
    link="http://api.duckduckgo.com/?q="+t+"&format=json&no_html=1"
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        duck=json.load(f)

        for key in duck.keys():
            if type(duck[key])!=list:
                params["duck_"+str(key)]=duck[key]
        params["RelatedTopics"]=[]
        flag=False
        duck_rel={}
        duck_rel["type"]="Similar"
        duck_rel["lis"]=[]
        for obj in duck["RelatedTopics"]:
            if "Name" not in obj.keys():
                flag=True
                duck_rel["lis"].append(obj)
        if flag:
            params["RelatedTopics"].append(duck_rel)

        for obj in duck["RelatedTopics"]:
            duck_rel={}
            if "Name" in obj.keys():
                flag=True
                duck_rel["type"]=obj["Name"]
                duck_rel["lis"]=[]
                for it in obj["Topics"]:
                    duck_rel["lis"].append(it)
                params["RelatedTopics"].append(duck_rel)

        if not(flag):
            params["error_"]="ahh !! Keyword not found try another one"

    except:
        params["error_"]="Oops something went wrong"


def html_to_text(data):        
    # remove the newlines
    data = data.replace("\n", " ")
    data = data.replace("\r", " ")
   
    # replace consecutive spaces into a single one
    data = " ".join(data.split())   
   
    # remove all the tags
    p = re.compile(r'<[^<]*?>')
    data = p.sub('', data)
   
    return data

#CrunchBase
def cb(term):
    term=term.replace(" ", "-")
    link="http://api.crunchbase.com/v/1/company/"+term+".js?api_key="+CB_API_KEY
    print link
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)       

        params["cb_overview"]=html_to_text(d['overview'])
        params["cb_name"]=d['name']
        params["cb_homeurl"]=d['homepage_url']
        params["cb_url"]=d['crunchbase_url']
        params["cb_category"]=d['category_code']

    except:
        params["cb_name"]=None


#Twitter
def twit(term):
    term=term.replace(" ", "")
    link="http://search.twitter.com/search.json?q=%23"+term
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)
    except:
        return None
    length=len(d['results'])
    i=1
    answer=""
    if length<10:
        for i in range(1,length):
             params["twitter"+str(i)]=d['results'][i]['text']
    else:
        for i in range(1,10):
             params["twitter"+str(i)]=d['results'][i]['text']
    #params["twitter"]=answer

#IMDB
def imdb(term):
    term=term.replace(" ","+")
  
    link="http://www.omdbapi.com/?s="+term
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        lis =json.load(f)
        links=[]
        for i in lis["Search"]:
            if i["imdbID"]:
                 links.append("http://www.omdbapi.com/?i="+i["imdbID"])      
        l=min(len(links),4)
       

        params["imdb"]=[]
        for i in range(l):
            req = urllib2.Request(links[i], None)
            f = opener.open(req)
            imdb =json.load(f)
            params["imdb"].append(imdb);
    except:
        params['imdb']=None

#gmaps
def gmaps(term):
    loc=term.replace(" ","+")
    link='http://maps.googleapis.com/maps/api/staticmap?center='+loc+'&zoom=12&size=600x300&maptype=roadmap&sensor=false&key='+GMAP_API_KEY
    try:
        infile = opener.open(link)
        page = infile.read()
    except:
        return None    
    return link

#fbparams=dict()

#Facebook
def faceb(term):
    term=term.replace(" ", "")
    try:
        link="http://graph.facebook.com/"+term
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)
        if 'error' in d:
            params['facebook_url']=None
           
        elif 'picture' in d:
            #return d['picture']+"<br>"+d['link']+"<br>"+d['about']+"<br>"+str(d['likes'])
            params['facebook_name']=term
            params['facebook_image']=d['picture']
            params['facebook_url']=d['link']
            params['facebook_about']=d['about']
            params['facebook_likes']=str(d['likes'])
            
        else:
            #return d['link']+"<br>"+d['about']+"<br>"+str(d['likes'])
            params['facebook_name']=term
            params['facebook_url']=d['link']
            params['facebook_about']=d['about']
            params['facebook_likes']=str(d['likes'])
            
    except:
        params['facebook_url']=None
        
    
#news
def news(term):
    t=[]
    l= []
    term=term.replace(" ", "-")
    link="http://news.google.com/news?q="+term+"&output=rss"
    try:
        from xml.dom.minidom import parseString
        file = urllib2.urlopen(link)
        data = file.read()
        file.close()
        dom = parseString(data)   
        for i in dom.getElementsByTagName('title'):
            xmlTag = i.toxml()
            t.append((xmlTag.replace('<title>','').replace('</title>','')))

        for i in dom.getElementsByTagName('link'):
            xmlTag1 = i.toxml()
            l.append((xmlTag1.replace('<link>','').replace('</link>','')))

        params["newsitem"]=[]
        if len(l)>2:
            for i in xrange(2,len(l)):
                news_dict={}
                news_dict["content"]=t[i]
                
                Istart=l[i].find("url=")
                if Istart!=-1:
                    news_dict["link"]=(l[i][Istart+4:])
                params["newsitem"].append(news_dict)
                if i==15:
                    break;
    except:
        params["newsitem"]=None



#quora
def quora(w):
    k=str(w)
    l=k.lower()
    t=l.replace (" ", "+")
    params["quora"]= "http://www.quora.com/search?q="+t


#Youtube
def youtube(term):
    term=term.replace(" ","+")
    params["yt"]=[]
    link="https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&key="+YouTube_API_KEY+"&q="+term
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        yt =json.load(f)

        for it in yt["items"]:
            vid={}
            vid["id"]=it["id"]["videoId"]
            vid["title"]=it["snippet"]["title"]
            vid["time"]=it["snippet"]["publishedAt"]
            vid["description"]=it["snippet"]["description"]
            vid["thumbnails"]=it["snippet"]["thumbnails"]["medium"]["url"]
            params["yt"].append(vid)
       
    except:
        params["yt"]=None
        
    
class MainPage(BaseHandler):
    def get(self):
        self.render("search-form.html")

    def post(self):
        q=self.request.get("q")
        
        #params = dict(q=q)
        qs=q.strip()
        topic_summary(qs)
        cb(qs)
        
        txt=wiki.extractwiki(qs)
        if txt!=None:
            params["wiki_"]=txt
        else:
            params["wiki_"]=None
        # p3=twit(qs)
        imdb(qs)
        # img_url=gmaps(qs)
        faceb(qs)
        # p6=iris(qs)
        quora(qs)
        youtube(qs)
        news(qs)
               
        
        self.render('results.html', **params)

        # if img_url:
        #     self.write('<br><br><h1> Results maps</h1>'+ '<img src="'+img_url+'" >')
        
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
