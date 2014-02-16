__author__ = 'Jeremy'
import sys,os
import datetime
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
#counter for related pages
RELCNT=0
keyWords=[]
#configure total number of downloading threads
THREADCOUNT=15
#counter for currently crawled pages
CRAWEDSIZE=0
#record total number to by downloaded, specified by user input parameter
TOTSIZE=0
#visited dictionary, to detect duplicated url
visited=set()
#counter for total number of 404 encountered
TOTAL404=0

def writeRepo(curPage,keyWords):
    try:
        global RELCNT
        keyString='&'.join(keyWords)
        REPOFILE=open('REPOLIST_'+keyString,'a')
        REPOFILE.write(','.join([curPage['url'],'200''Priority: '+str(curPage['priority']),'Score: '+str(curPage['score']),curPage['time']])+'\n')
        REPOFILE.close()
        if not os.path.exists(keyString):
            os.mkdir(keyString)
        pageFile=open(keyString+'/'+curPage['url'].replace('/',':'),'w')
        pageFile.write(curPage.get('data'))
        pageFile.close()
        if curPage.get('score')>0:
            RELCNT+=1

    except IOError:
        print 'Failed to write page data to File'


def getSeeds(keyWords):
    """
    @para keyWords : user input key words
    @return seeds : list of url objects
    This function takes in key words from user input parameter, ask google for top 10 search results and return them
    these initial urls have highest priority : 0
    """
    keyString='%20'.join(keyWords)
    #check cache first :-)
    # Note: cache is not actually working for now, need another daemon process to keep cached data in mem. Or use a file in OS
    cache=JCache()
    seeds = cache.find(keyString)
    if seeds:
        print JColors.OKBLUE+''+str(len(seeds))+' seeds fetched successfully from cache!'
        return seeds
    #compose google api url
    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='+keyString+'&userip=74.64.18.187&rsz=4&start='
    print JColors.OKBLUE+'--Composed query URL:'+url
    #loop for 10 urls for given keywords from google, need loop since google returns only 4 results at a time, and cursor to next 4.
    seeds=[]
    start = 0
    while len(seeds)<10:
        time.sleep(2) # sleep here to reduce impact to google, also avoid getting banned.
        try:
            request = urllib2.Request(url+str(start), None)
            response = urllib2.urlopen(request)
            results = simplejson.load(response)
            print JColors.OKBLUE+'Results fetched successfully!'
            print results
            for res in results['responseData']['results']:
                seeds.append(res['url'])
                if len(seeds)>=10:
                    break
        except Exception:
            print JColors.WARNING+"Something is wrong!"
            import traceback
            print traceback.print_exc()
            sys.exit(0)
        start=start+4
    print JColors.OKBLUE+''+str(len(seeds))+' seeds fetched successfully!'
    #update cache
    cache.put(keyString,seeds)
    return seeds


def isVisited(url):
    """
    helper function to test if given url is visited
    """
    return url['url'] in visited


def downloadPage(q,pq):
    """
    @para q : Priority queue storing url objects, priority is calculated by : pri=pri_of_current_page+10-#keywords_appeared_in_url
    @para pq: queue storing downloaded page objects
    This function fetched url from priority queue, checks 1. if it's visited 2. check if url returns 404 3. check MIME type
    4.download page if previous conditions are satisfied.
    This function will be put into multiple threads, so a synchronized priority queue is used.
    """
    global CRAWEDSIZE,TOTSIZE,TOTAL404,keyWords
    while True:
        #check if q has more urls to get, sleep 3 seconds if q is empty
        if q.qsize()<1:
                print JColors.BOLD+'Download thread: No more URL to download, go to sleep...'
                time.sleep(3)
                continue
        #stop if enough pages are downloaded
        if CRAWEDSIZE+pq.qsize()>=TOTSIZE:
            return
        print JColors.OKBLUE+'Downloader: Start fetching from URL...'
        curUrl=dict()
        #fetch next un-visited url
        while q.qsize()>0:
            curUrl = q.get()[1];
            if not isVisited(curUrl):
                break
        #start downloading
        if curUrl and not isVisited(curUrl):
            try:
                response=urllib2.urlopen(curUrl['url'],timeout=5) #timeout 5 sec to avoid 'stucking' into some un-responding pages
                if response.code==404:
                    TOTAL404+=1
                    JLogger.log('Got a 404 response!')
                if response.code==200 and response.info().type=='text/html':#only download pages with code 200 and MIME type html
                    page_item=dict()
                    page_item['url']=curUrl['url']
                    page_item['time']=str(datetime.datetime.now())
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


def parsePage(q,pq):
    """
    @para q : Priority queue storing url objects, priority is calculated by : pri=pri_of_current_page+10-#keywords_appeared_in_url
    @para pq: queue storing downloaded page objects
    1. parse URL from page
    2. save page and meta data into repofile
    3. calculate actual score of a page by : Sum(# of key word appearance in a page)
    """
    global CRAWEDSIZE,TOTSIZE,keyWords
    while True:
        # fetch page data from pq to parse, go to sleep if pq is empty
        if pq.qsize()<1:
            print JColors.BOLD+'Parser thread: No more page to parse, go to sleep...'
            time.sleep(3)
            continue
        if CRAWEDSIZE+pq.qsize()>=TOTSIZE or q.qsize()>1.5*TOTSIZE:
            return
        print JColors.OKBLUE+'Parser: fetching and parsing page...'
        curPage=pq.get()
        data=curPage['data']

        #===================================================
        #for test & debug: save current processing page to file
        try:
            temp=open('PROCESSINGFILE','w')
            temp.write(data)
            temp.close()
        except IOError:
            print 'Failed to open PROCESSINGFILE'
        #===================================================

        lines=data.splitlines()
        score=0
        #process line by line
        for line in lines:
            #add line score to page score
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
                # parse robots.txt
                rp=robotparser.RobotFileParser()
                rp.set_url(urlItem.get('domain')+'/robots.txt')
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
        writeRepo(curPage,keyWords)
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
        writeRepo(page,keyWords)
    stat.report(TOTAL404,RELCNT,keyWords)


if __name__=="__main__":

    main()
