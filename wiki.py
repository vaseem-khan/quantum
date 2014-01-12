#!/usr/bin/env python

import re
import yaml
import urllib
import urllib2

class WikipediaError(Exception):
    pass

class Wikipedia:
    url_article = 'http://%s.wikipedia.org/w/index.php?action=raw&title=%s'
    url_image = 'http://%s.wikipedia.org/w/index.php?title=Special:FilePath&file=%s'
    url_search = 'http://%s.wikipedia.org/w/api.php?action=query&list=search&srsearch=%s&sroffset=%d&srlimit=%d&format=yaml'
    
    def __init__(self, lang):
        self.lang = lang
    
    def __fetch(self, url):
        request = urllib2.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            result = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            raise WikipediaError(e.code)
        except urllib2.URLError, e:
            raise WikipediaError(e.reason)
        
        return result
    
    def article(self, article):
        url = self.url_article % (self.lang, urllib.quote_plus(article))
        content = self.__fetch(url).read()
        
        if content.upper().startswith('#REDIRECT'):
            match = re.match('(?i)#REDIRECT \[\[([^\[\]]+)\]\]', content)
            
            if not match == None:
                return self.article(match.group(1))
            
            raise WikipediaError('Can\'t found redirect article.')
        
        return content
    
    def image(self, image, thumb=None):
        url = self.url_image % (self.lang, image)
        result = self.__fetch(url)
        content = result.read()
        
        if thumb:
            url = result.geturl() + '/' + thumb + 'px-' + image
            url = url.replace('/commons/', '/commons/thumb/')
            url = url.replace('/' + self.lang + '/', '/' + self.lang + '/thumb/')
            
            return self.__fetch(url).read()
        
        return content
    
    def search(self, query, page=1, limit=10):
        offset = (page - 1) * limit
        url = self.url_search % (self.lang, urllib.quote_plus(query), offset, limit)
        content = self.__fetch(url).read()
        
        parsed = yaml.load(content)
        search = parsed['query']['search']
        
        results = []
        
        if search:
            for article in search:
                title = article['title'].strip()
                
                snippet = article['snippet']
                snippet = re.sub(r'(?m)<.*?>', '', snippet)
                snippet = re.sub(r'\s+', ' ', snippet)
                snippet = snippet.replace(' . ', '. ')
                snippet = snippet.replace(' , ', ', ')
                snippet = snippet.strip()
                
                wordcount = article['wordcount']
                
                results.append({
                    'title' : title,
                    'snippet' : snippet,
                    'wordcount' : wordcount
                })
        
        # yaml.dump(results, default_style='', default_flow_style=False,
        #     allow_unicode=True)
        return results
class Wiki2Plain:
    def __init__(self, wiki):
        self.wiki = wiki
        
        self.text = wiki
        self.text = self.unhtml(self.text)
        self.text = self.unwiki(self.text)
        self.text = self.punctuate(self.text)
    
    def __str__(self):
        return self.text
    
    def unwiki(self, wiki):
        """
        Remove wiki markup from the text.
        """
        wiki = re.sub(r'(?i)\{\{IPA(\-[^\|\{\}]+)*?\|([^\|\{\}]+)(\|[^\{\}]+)*?\}\}', lambda m: m.group(2), wiki)
        wiki = re.sub(r'(?i)\{\{Lang(\-[^\|\{\}]+)*?\|([^\|\{\}]+)(\|[^\{\}]+)*?\}\}', lambda m: m.group(2), wiki)
        wiki = re.sub(r'\{\{[^\{\}]+\}\}', '', wiki)
        wiki = re.sub(r'(?m)\{\{[^\{\}]+\}\}', '', wiki)
        wiki = re.sub(r'(?m)\{\|[^\{\}]*?\|\}', '', wiki)
        wiki = re.sub(r'(?i)\[\[Category:[^\[\]]*?\]\]', '', wiki)
        wiki = re.sub(r'(?i)\[\[Image:[^\[\]]*?\]\]', '', wiki)
        wiki = re.sub(r'(?i)\[\[File:[^\[\]]*?\]\]', '', wiki)
        wiki = re.sub(r'\[\[[^\[\]]*?\|([^\[\]]*?)\]\]', lambda m: m.group(1), wiki)
        wiki = re.sub(r'\[\[([^\[\]]+?)\]\]', lambda m: m.group(1), wiki)
        wiki = re.sub(r'\[\[([^\[\]]+?)\]\]', '', wiki)
        wiki = re.sub(r'(?i)File:[^\[\]]*?', '', wiki)
        wiki = re.sub(r'\[[^\[\]]*? ([^\[\]]*?)\]', lambda m: m.group(1), wiki)
        wiki = re.sub(r"''+", '', wiki)
        wiki = re.sub(r'(?m)^\*$', '', wiki)
        
        return wiki
    
    def unhtml(self, html):
        """
        Remove HTML from the text.
        """
        html = re.sub(r'(?i)&nbsp;', ' ', html)
        html = re.sub(r'(?i)<br[ \\]*?>', '\n', html)
        html = re.sub(r'(?m)<!--.*?--\s*>', '', html)
        html = re.sub(r'(?i)<ref[^>]*>[^>]*<\/ ?ref>', '', html)
        html = re.sub(r'(?m)<.*?>', '', html)
        html = re.sub(r'(?i)&amp;', '&', html)
        
        return html
    
    def punctuate(self, text):
        """
        Convert every text part into well-formed one-space
        separate paragraph.
        """
        text = re.sub(r'\r\n|\n|\r', '\n', text)
        text = re.sub(r'\n\n+', '\n\n', text)
        
        parts = text.split('\n\n')
        partsParsed = []
        
        for part in parts:
            part = part.strip()
            
            if len(part) == 0:
                continue
            
            partsParsed.append(part)
        
        return '\n\n'.join(partsParsed)
    
    def image(self):
        """
        Retrieve the first image in the document.
        """
        # match = re.search(r'(?i)\|?\s*(image|img|image_flag)\s*=\s*(<!--.*-->)?\s*([^\\/:*?<>"|%]+\.[^\\/:*?<>"|%]{3,4})', self.wiki)
        match = re.search(r'(?i)([^\\/:*?<>"|% =]+)\.(gif|jpg|jpeg|png|bmp)', self.wiki)
        
        if match:
            return '%s.%s' % match.groups()
        
        return None

def extractwiki(w):
    wiki = Wikipedia('simple')
    try :
        raw=wiki.article(w)
    except:
        raw=None
    if raw:
        wiki2plain = Wiki2Plain(raw)
        content = wiki2plain.text
        return content.decode("utf8")
    return None


