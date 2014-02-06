__author__ = 'admin'
import JLogger
from JColors import JColors

def writeRepo(curPage):
    try:
        REPOFILE=open('REPOFILE','a')
        REPOFILE.write('This page is level: '+str(curPage['level']))
        REPOFILE.write(curPage.get('data')+'\n')
        REPOFILE.close()

    except IOError:
        print 'Failed to write from pq to File'

