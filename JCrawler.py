__author__ = 'Jeremy'
import sys
import urllib2,urllib
import simplejson
from JColors import JColors
import JLogger
from collections import deque
import time
import threading
DEBUG = True
CRAWEDSIZE=0
TOTSIZE=0
#visited dictionary
visited=set()

def getSeeds(keyWords):
    #compose url
    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='+'%20'.join(keyWords)+'&userip=74.64.18.187&rsz=4&start='
    print JColors.OKBLUE+'--Composed query URL:'+url
    #loop for 10 urls for given keywords    from google
    seeds = []
    start = 0
    while len(seeds)<10:
        try:
            request = urllib2.Request(url+str(start), None)
            response = urllib2.urlopen(request)
            results = simplejson.load(response)
            print JColors.OKBLUE+'Results fetched successfully!'
            for res in results['responseData']['results']:
                seeds.append(res['url'])
                # print res['url']
                if len(seeds)>=10:
                    break
        except Exception:
            print JColors.WARNING+"Something is wrong!"
            import traceback
            print traceback.print_exc()
            sys.exit(0)
        start=start+4
        #print seeds
    print JColors.OKBLUE+''+str(len(seeds))+' seeds fetched successfully!'
    return seeds


def isVisited(url):
    return url['url'] in visited

def downloadPage(q,pq):
    global CRAWEDSIZE,TOTSIZE
    while True:
        if len(q)<1:
                print JColors.BOLD+'Download thread: No more URL to download, go to sleep...'
                time.sleep(3)
                continue
        # JLogger.log(JColors.OKBLUE+'Downloader: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))
        print JColors.OKBLUE+'Downloader: Start fetching URL...'
        curUrl=''
        while len(q)>0 and CRAWEDSIZE<TOTSIZE:
            curUrl = q.popleft();
            if not isVisited(curUrl):
                break
        if curUrl and not isVisited(curUrl):
            try:
                response=urllib.urlopen(curUrl['url'])
                if response.code==200:
                    item=dict()
                    item['data']=response.read()
                    response.close()
                    item['level']=curUrl['level']
                    pq.append(item)
                    JLogger.log(JColors.OKGREEN+'Download '+curUrl['url']+' succeeded!')
            except Exception:
                JLogger.log(JColors.WARNING+'Download '+curUrl['url']+' failed!')

# 1. parse URL from page
# 2. save page and meta data into repofile
def parsePage(q,pq):
    global CRAWEDSIZE,TOTSIZE

    while True:
        if len(pq)<1:
            print JColors.BOLD+'Parser thread: No more page to parse, go to sleep...'
            time.sleep(3)
            continue
        if CRAWEDSIZE>=TOTSIZE:
            return
        # JLogger.log(JColors.OKBLUE+'Parser: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))
        print JColors.OKBLUE+'Parser: fetching and parsing page...'
        curPage=pq.popleft()
        data=curPage['data']
        lines=data.splitlines()
        for line in lines:
            n=line.find('href')
            if n!=-1:
                url=line[n:-1].split('"')[1]
                urlItem=dict()
                urlItem['url']=url
                urlItem['level']=curPage['level']+1
                q.append(urlItem)
                JLogger.log(JColors.OKGREEN+'Parser: new URL '+url+' added to URL queue!')
        #wirte page to file and increase counter
        JLogger.log(JColors.OKBLUE+'Parser: writing processed page...')
        try:
            REPOFILE=open('REPOFILE','a')
            REPOFILE.write(data+'\n')
            REPOFILE.close()
            CRAWEDSIZE=CRAWEDSIZE+1
            JLogger.log(JColors.OKBLUE+'Parser: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))
        except IOError:
            print JColors.FAIL+'Failed to open repo file!'

def main():
    #get agvs
    global TOTSIZE
    try:
        keyWords = sys.argv[1:-1]
        TOTSIZE = int(sys.argv[-1])
    except Exception:
        print JColors.FAIL+"input arguments format: keyword1 keyword2 ... seedSize"
        sys.exit(0)

    seeds = getSeeds(keyWords)

    #put em in a queue
    q=deque()
    for s in seeds:
        item = dict()
        item['url']=s
        # item['status']='unvisited'
        item['level']=0
        q.append(item)

    #downloaded pages queue
    pq=deque()

    downloadThread = threading.Thread(target=downloadPage(q,pq))
    parseThread = threading.Thread(target=parsePage(q,pq))
    downloadThread.start()
    parseThread.start()


if __name__=="__main__":
    main()