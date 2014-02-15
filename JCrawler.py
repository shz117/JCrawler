__author__ = 'Jeremy'
import sys
import urllib2
import robotparser
import simplejson
from JColors import JColors
import JLogger
from Queue import PriorityQueue as PQ,Queue
import time
import threading
from JStats import JStats
from JCache import JCache
import JRepowriter
keyWords=[]
THREADCOUNT=15
DEBUG = True
CRAWEDSIZE=0
TOTSIZE=0
#visited dictionary
visited=set()
TOTAL404=0

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
    global CRAWEDSIZE,TOTSIZE,TOTAL404,keyWords
    while True:
        if q.qsize()<1:
                print JColors.BOLD+'Download thread: No more URL to download, go to sleep...'
                time.sleep(3)
                continue
        # JLogger.log(JColors.OKBLUE+'Downloader: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))
        if CRAWEDSIZE+pq.qsize()>=TOTSIZE:
            return
        print JColors.OKBLUE+'Downloader: Start fetching from URL...'
        curUrl=dict()
        while q.qsize()>0:
            curUrl = q.get()[1];
            if not isVisited(curUrl):
                break
        if curUrl and not isVisited(curUrl):
            try:
                response=urllib2.urlopen(curUrl['url'],timeout=5)
                if response.code==404:
                    TOTAL404+=1
                    JLogger.log('Got a 404 response!')
                if response.code==200 and response.info().type=='text/html':
                    page_item=dict()
                    page_item['data']=response.read()
                    response.close()
                    page_item['domain']=curUrl['domain']
                    page_item['priority']=curUrl['priority']
                    page_item['score']=-1
                    pq.put(page_item,False)
                    JLogger.log(JColors.OKGREEN+'Download '+curUrl['url']+' succeeded!')
                    print 'pq length:'+str(pq.qsize())
            except Exception:
                JLogger.log(JColors.WARNING+'Download '+curUrl['url']+' failed!')

# 1. parse URL from page
# 2. save page and meta data into repofile
# 3. find actuall score
def parsePage(q,pq):
    global CRAWEDSIZE,TOTSIZE,keyWords
    while True:
        if pq.qsize()<1:
            print JColors.BOLD+'Parser thread: No more page to parse, go to sleep...'
            time.sleep(3)
            continue
        if CRAWEDSIZE+pq.qsize()>=TOTSIZE or q.qsize()>1.5*TOTSIZE:
            return
        # JLogger.log(JColors.OKBLUE+'Parser: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))
        print JColors.OKBLUE+'Parser: fetching and parsing page...'
        curPage=pq.get()
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
        score=0
        for line in lines:
            for wd in keyWords:
                score+=line.count(wd)
            n=line.find('href')
            if CRAWEDSIZE<=TOTSIZE and n!=-1:
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
                try:
                    rp.read()
                    if not rp.can_fetch('*',url):
                        print JColors.WARNING+''+url+' Forbidden by robot.txt, skipped!'
                        continue
                except Exception:
                    print "Load robot failed"
                urlItem['url']=url
                # calculate url priority : according to keyword count in url itself
                url_priority=curPage['priority']+10
                for wd in keyWords:
                    url_priority-url.count(wd)
                urlItem['priority']=url_priority
                q.put((url_priority,urlItem))
                print q.qsize()
                if q.qsize()>1.5*TOTSIZE:
                    return
                JLogger.log(JColors.OKGREEN+'Parser: new URL '+url+' added to URL queue! Priority:'+str(url_priority))
        #wirte page to file and increase counter
        curPage['score']=score
        JLogger.log(JColors.OKBLUE+'Parser: writing processed page...')
        JRepowriter.writeRepo(curPage,keyWords)
        CRAWEDSIZE=CRAWEDSIZE+1
        JLogger.log(JColors.OKBLUE+'Parser: Current craw status '+str(CRAWEDSIZE)+'/'+str(TOTSIZE))

def calcScore(page):
    data=page['data']
    lines=data.splitlines()
    score=0
    for line in lines:
        for wd in keyWords:
            score+=line.count(wd)
    page['score']=score

def main():
    #get agvs
    global TOTSIZE,THREADCOUNT,TOTAL404,keyWords
    try:
        keyWords = sys.argv[1:-1]
        TOTSIZE = int(sys.argv[-1])
    except Exception:
        print JColors.FAIL+"input arguments format: keyword1 keyword2 ... seedSize"
        sys.exit(0)

    seeds = getSeeds(keyWords)

    #put em in a queue
    q=PQ()
    for s in seeds:
        item = dict()
        item['url']=s
        # item['status']='unvisited'
        lst=s.split('/')
        item['priority']=0
        item['domain']=lst[0]+'//'+lst[2]
        try:
            q.put((item['priority'],item))
        except Exception:
            print 'This is never gonna happen...'

    #downloaded pages queue
    pq=Queue()

    stat=JStats(TOTSIZE)
    parseThread = threading.Thread(target=parsePage,args=(q,pq))
    parseThread.start()
    # parseThread.join()
    for i in range(1,THREADCOUNT):
        downloadThread = threading.Thread(target=downloadPage,args=(q,pq))
        downloadThread.start()
        downloadThread.join()

    JLogger.log(JColors.OKBLUE+'Parser: got enough page, writing pages in queue to REPOFILE...')
    while not pq.empty():
        page=pq.get()
        if page['score']==-1: calcScore(page)
        JRepowriter.writeRepo(page,keyWords)
    stat.report(TOTAL404)


if __name__=="__main__":

    main()
