__author__ = 'admin'
import time
import os
import JLogger
from JColors import JColors
class JStats:
    def __init__(self,TOTSIZE):
        self.start=time.time()
        self.TOTSIZE=TOTSIZE
        print 'Time start!'
    def report(self,TOTAL404,RELCNT,keyWords):
        keyString='&'.join(keyWords)
        fsize=str(self.get_size(keyString)>>20)+'Mb'
        elapsed_time = time.time() - self.start
        JLogger.log(JColors.BOLD+'Total crawled file size:')
        JLogger.log(JColors.BOLD+fsize)
        print 'Total 404 encountered: '+str(TOTAL404)
        JLogger.log(JColors.BOLD+'Total crawling time:')
        JLogger.log(str(elapsed_time))
        JLogger.log(JColors.BOLD+'Avg time per page:')
        JLogger.log(str(elapsed_time/self.TOTSIZE))
        JLogger.log(JColors.BOLD+'Total related page count:')
        JLogger.log(str(RELCNT))
        JLogger.log(JColors.BOLD+'Precision :')
        JLogger.log(str(RELCNT/(self.TOTSIZE*1.0)))
        try:
            repoList=open('REPOLIST_'+keyString,'a')
            repoList.write(
                '\n'.join(['Total crawled file size:',fsize,'Total 404 encountered:',str(TOTAL404),'Total crawling time:',
                           str(elapsed_time),'Avg time per page:',str(elapsed_time/self.TOTSIZE),'Total related page count:',
                           str(RELCNT),'Precision :',str(RELCNT/(self.TOTSIZE*1.0))])
            )
        except IOError:
            print 'Failed to write statistics to repolist file!'

    def get_size(self,start_path = '.'):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size