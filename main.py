import os
import webapp2
import cgi
import json
import jinja2
import urllib2
import re
from google.appengine.ext import db

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
#duck duck go
def topic_summary(w):
    k=str(w)
    params["Keyword"]=k
    l=k.lower()
    t=l.replace (" ", "+")        
    link="http://api.duckduckgo.com/?q="+t+"&format=json&pretty=1"
    f=[]
    d=[]
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)
    except:
        return None

    ret=""
    if d["Definition"]=="":
        params["duck_defination"]=None
    else:
        params["duck_defination"]= d["Definition"]
    if d["AbstractText"]=="":
        params["duck_abstract"]=None        
    else:
        params["duck_abstract"]=d["AbstractText"]
    length= len(d["RelatedTopics"])
    i=0;
    params['duck_image']=None
    if  d["Image"]!="":
        params['duck_image']=d["Image"]
    else:
         params['duck_image']=None
    try:
        if d["RelatedTopics"][0]["Icon" ]["URL"]!="":
            params['duck_image']=d["RelatedTopics"][0]["Icon" ]["URL"]        
    except:
        params['duck_image']=None
    
    params["duck_related"]=[]
    if length<10:
        for i in range(1,length):
            if "Result" in d["RelatedTopics"][i] and d["RelatedTopics"][i]["Text"]!="":
                params["duck_related"].append(d["RelatedTopics"][i]["Text"])
            elif  'Topics' in d["RelatedTopics"][i]:
                l2=len(d["RelatedTopics"][i]["Topics"])
                k=0
                while k<l2 and i<11:
                    if  "Result" in d["RelatedTopics"][i]["Topics"][k] and  d["RelatedTopics"][i]["Topics"][k]["Text"]!="":
                        params["duck_related"].append(d["RelatedTopics"][i]["Topics"][k]["Text"])
                    k+=1
                    
    else:
        for i in range(1,10):
            if "Result" in d["RelatedTopics"][i] and d["RelatedTopics"][i]["Text"]!="":
                params["duck_related"].append(d["RelatedTopics"][i]["Text"])
            elif  'Topics' in d["RelatedTopics"][i]:
                l2=len(d["RelatedTopics"][i]["Topics"])
                k=0
                while k<l2 and k+i<11:
                    if  "Result" in d["RelatedTopics"][i]["Topics"][k] and d["RelatedTopics"][i]["Topics"][k]["Text"]!="" :
                        params["duck_related"].append(d["RelatedTopics"][i]["Topics"][k]["Text"])
                    k+=1
    return params
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
    link="http://api.crunchbase.com/v/1/company/"+term+".js"
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)
    except:
        params["cb_name"]=None
        return None
    if 'error' in d:
        params["cb_name"]=None
        return None
    else:
        params["cb_overview"]=(d['overview'])
        params["cb_name"]=d['name']
        params["cb_url"]=d['homepage_url']
        params["cb_category"]=d['category_code']
        return params

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
    return params

#IMDB
def imdb(term):
    term=term.replace(" ","+")
    link="http://www.deanclatworthy.com/imdb/?q="+term
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)        
        if 'error' in d:
            params['imdb_title']=None
            return None
        elif 'runtime' and 'year' not in d:
            #return d['title']+"<br>"+d['rating']+"<br>"+d['genres']+"<br>"+d['imdburl']
            params['imdb_title']=d['title']
            params['imdb_rating']=d['rating']
            params['imdb_genres']=d['genres']
            params['imdb_imdburl']=d['imdburl']
            return params
        else:
            #return d['title']+"<br>"+d['rating']+"<br>"+d['runtime']+"<br>"+d['genres']+"<br>"+d['year']+"<br>"+d['imdburl']
            params['imdb_title']=d['title']
            params['imdb_rating']=d['rating']
            params['imdb_runtime']=d['runtime']
            params['imdb_genres']=d['genres']
            params['imdb_year']=d['year']
            params['imdb_imdburl']=d['imdburl']
            return params
    except:
        params['imdb_title']=None
        return None

#gmaps
def gmaps(term):
    loc=term.replace(" ","+")
    link='http://maps.googleapis.com/maps/api/staticmap?center='+loc+'&zoom=12&size=600x300&maptype=roadmap&sensor=false&key=AIzaSyBAspYdcOeGNE_gKhbLtOTrIUwqKByrJ9M'
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
            return None
        elif 'picture' in d:
            #return d['picture']+"<br>"+d['link']+"<br>"+d['about']+"<br>"+str(d['likes'])
            params['facebook_name']=term
            params['facebook_image']=d['picture']
            params['facebook_url']=d['link']
            params['facebook_about']=d['about']
            params['facebook_likes']=str(d['likes'])
            return params
        else:
            #return d['link']+"<br>"+d['about']+"<br>"+str(d['likes'])
            params['facebook_name']=term
            params['facebook_url']=d['link']
            params['facebook_about']=d['about']
            params['facebook_likes']=str(d['likes'])
            return params
    except:
        params['facebook_url']=None
        return None

#TechIRIS
def iris(term):
    term=term.replace(" ", "")
    link="http://thetechiris.com/api/get_search_results/?dev=1&search="+term
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)
    except:
        return None
    if d['count']==0:
        return None
    elif d['count']>=2:
        params["ti_post0_title"]=d['posts'][0]['title']
        params["ti_post0_url"]=d['posts'][0]['url']
        params["ti_post1_title"]=d['posts'][1]['title']
        params["ti_post1_title"]=d['posts'][1]['url']
        return params
    else:
        params["ti_post0_title"]=d['posts'][0]['title']
        params["ti_post0_url"]=d['posts'][0]['url']
        return params
    
#Free dictionary
def fdictionary(w):
    k=str(w);
    l=k.lower()
    t=l.replace (" ", "+")        
    link="http://api.duckduckgo.com/?q=define+"+t+"&format=json&pretty=1"
    try:
        req = urllib2.Request(link, None)
        f = opener.open(req)
        d=json.load(f)
    except:
        return None
    if d["Abstract"]!="":
        #return d["Abstract"]
        params["freeDict"]=d["Abstract"]
        return params

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
    except:
        return None
   
    for i in dom.getElementsByTagName('title'):
        xmlTag = i.toxml()
        t.append((xmlTag.replace('<title>','').replace('</title>','')))
    
    for i in dom.getElementsByTagName('link'):
        xmlTag1 = i.toxml()
        l.append((xmlTag1.replace('<link>','').replace('</link>','')))
  
    params["newsitem"]=[]
    params["newslink"]=[]
    if len(l)>2:
        for i in xrange(2,len(l)):
            params["newsitem"].append(t[i])
            params["newslink"].append(l[i])
           
    return params


#quora
def quora(w):
    k=str(w)
    l=k.lower()
    t=l.replace (" ", "+")        
    #return "http://www.quora.com/search?q="+t+"&context_type=&context_id="
    params["quora"]= "http://www.quora.com/search?q="+t+"&context_type=&context_id="
    return params


#Youtube
def youtube(w):
    k=str(w)
    l=k.lower()
    t=l.replace (" ", "+")
    params["youtube"]="http://www.youtube.com/results?search_query="+t
    #return "http://www.youtube.com/results?search_query="+t
    return params
    
class MainPage(BaseHandler):
    def get(self):
        self.render("search-form.html")

    def post(self):
        q=self.request.get("q")
        
        #params = dict(q=q)
        qs=q.strip()
        p=topic_summary(qs)
        p2=cb(qs)
        p3=twit(qs)
        p4=imdb(qs)
        img_url=gmaps(qs)
        p5=faceb(qs)
        p6=iris(qs)
        p7=fdictionary(qs)
        p8=quora(qs)
        p9=youtube(qs)
        p10=news(qs)
               
        """if p:
            self.write("<h1> Results wiki</h1>"+p)
        if p10:
            self.write('<br><h1>News</h1> '+p10)
        if p2:
            self.write("<br><br><h1> Results CB</h1>"+p2)
        if p3:
            self.write("<br><br><h1> Results Twitter</h1>"+p3)
        if p4:
            #self.write("<br><br><h1> Results IMDB</h1>"+p4)"""
        self.render('results.html', **params)
        if img_url:
            self.write('<br><br><h1> Results maps</h1>'+ '<img src="'+img_url+'" >')
        """if p5:
            self.write("<br><br><h1> Results Fb</h1>"+p5)
            self.render('results.html', **fbparams)
        if p6:
            self.write("<br><br><br><br><br><br><br><br<br><br><br><br><br><br><h1> Results TechIRIS</h1>"+p6)
        if p7:
            self.write("<br><br><h1>Free Dictionary </h1>"+p7)
        if p8:
            self.write('<br><h3>search on quora <a href="'+p8+'">'+q+'</a><h3>')
        if p9:
            self.write('<br><h3>search on youtube <a href="'+p9+'">'+q+'</a><h3>')"""
        

        if not p and not p2 and not p3 and not p4 and not img_url and not p5 and not p6 and not p7 and not p8 and not p9:
            params['error_q']="That's not a valid term!"
            self.render('search-form.html', **params)    

        
app = webapp2.WSGIApplication([('/', MainPage)], debug=True)
