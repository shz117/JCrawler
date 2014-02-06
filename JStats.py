__author__ = 'admin'
import time
import JLogger
from JColors import JColors
class JStats:
    def __init__(self,TOTSIZE):
        self.start=time.time()
        self.TOTSIZE=TOTSIZE
        print 'Time start!'
    def report(self):
        elapsed_time = time.time() - self.start
        JLogger.log(JColors.BOLD+'Totoal crawling time:')
        JLogger.log(str(elapsed_time))
        JLogger.log(JColors.BOLD+'Avg time per page:')
        JLogger.log(str(elapsed_time/self.TOTSIZE))