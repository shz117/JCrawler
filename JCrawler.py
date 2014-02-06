__author__ = 'Jeremy'
import sys
import urllib2,urllib
import robotparser
import simplejson
from JColors import JColors
import JLogger
from collections import deque
import time
import threading
from JStats import JStats
from JCache import JCache
import JRepowriter
THREADCOUNT=15
DEBUG = True
CRAWEDSIZE=0
TOTSIZE=0
#visited dictionary
visited=set()

def getSeeds(keyWords):
    keyString='%20'.join(keyWords)
    #check cache first :-)
    cache=JCache()
    seeds = cache.find(keyString)
    if seeds:
        print JColors.OKBLUE+''+str(len(seeds))+' seeds fetched successfully from cache!'
        return seeds
    #compose url
    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='+keyString+'&userip=74.64.18.187&rsz=4&start='
    print JColors.OKBLUE+'--Composed query URL:'+url
    #loop for 10 urls for given keywords    from google
    seeds=[]
    start = 0
    while len(seeds)<10:
        time.sleep(2)
        try:
            request = urllib2.Request(url+str(start), None)
            response = urllib2.urlopen(request)
            results = simplejson.load(response)
            print JColors.OKBLUE+'Results fetched successfully!'
            print results
            print type(results['responseData'])
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
    #update cache
    cache.put(keyString,seeds)
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
        if CRAWEDSIZE+len(pq)>=TOTSIZE:
            return
        print JColors.OKBLUE+'Downloader: Start fetching from URL...'
        curUrl=''
        while len(q)>0:
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
                    item['domain']=curUrl['domain']
                    pq.append(item)
                    JLogger.log(JColors.OKGREEN+'Download '+curUrl['url']+' succeeded!')
                    print 'pq length:'+str(len(pq))
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
        if CRAWEDSIZE+len(pq)>=TOTSIZE or len(q)>1.5*TOTSIZE:
            return
        # JLogger.log(JColors.OKBLUE+'Parser: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))
        print JColors.OKBLUE+'Parser: fetching and parsing page...'
        curPage=pq.popleft()
        data=curPage['data']

        #===================================================
        #for test: save current processing page to file
        try:
            temp=open('PROCESSINGFILE','w')
            temp.write(data)
            temp.close()
        except IOError:
            print 'Failed to open PROCESSINGFILE'
        #===================================================

        lines=data.splitlines()
        for line in lines:
            n=line.find('href')
            if n!=-1:
                ll=line[n:-1].split('"')
                if len(ll)>2:
                    url=ll[1]
                else:
                    continue
                urlItem=dict()
                if url.find('http')==-1:
                    url=curPage['domain']+url
                    urlItem['domain']=curPage['domain']
                else:
                    lst=url.split('/')
                    try:
                        urlItem['domain']=lst[0]+'//'+lst[2]
                    except Exception:
                        print lst
                rp=robotparser.RobotFileParser()
                rp.set_url(urlItem['domain']+'/robots.txt')
                rp.read()
                if not rp.can_fetch('*',url):
                    print JColors.WARNING+''+url+' Forbidden by robot.txt, skipped!'
                    continue
                urlItem['url']=url
                urlItem['level']=curPage['level']+1
                q.append(urlItem)
                print len(q)
                if len(q)>3*TOTSIZE:
                    return
                JLogger.log(JColors.OKGREEN+'Parser: new URL '+url+' added to URL queue!')
        #wirte page to file and increase counter
        JLogger.log(JColors.OKBLUE+'Parser: writing processed page...')
        JRepowriter.writeRepo(curPage)
        CRAWEDSIZE=CRAWEDSIZE+1
        JLogger.log(JColors.OKBLUE+'Parser: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))

def main():
    #get agvs
    global TOTSIZE,THREADCOUNT
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
        lst=s.split('/')
        item['domain']=lst[0]+'//'+lst[2]
        q.append(item)

    #downloaded pages queue
    pq=deque()

    stat=JStats(TOTSIZE)
    parseThread = threading.Thread(target=parsePage,args=(q,pq))
    parseThread.start()
    # parseThread.join()
    for i in range(1,THREADCOUNT):
        downloadThread = threading.Thread(target=downloadPage,args=(q,pq))
        downloadThread.start()
        downloadThread.join()

    JLogger.log(JColors.OKBLUE+'Parser: got enough page, writing pages in queue to REPOFILE...')
    for page in pq:
        JRepowriter.writeRepo(page)
    stat.report()


if __name__=="__main__":

    main()
