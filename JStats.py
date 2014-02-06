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
    def report(self):
        elapsed_time = time.time() - self.start
        JLogger.log(JColors.BOLD+'Total crawed file size:')
        JLogger.log(JColors.BOLD+str(os.path.getsize('REPOFILE')>>20)+'Mb')
        JLogger.log(JColors.BOLD+'Totoal crawling time:')
        JLogger.log(str(elapsed_time))
        JLogger.log(JColors.BOLD+'Avg time per page:')
        JLogger.log(str(elapsed_time/self.TOTSIZE))