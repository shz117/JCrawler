__author__ = 'admin'
import JLogger
from JColors import JColors

def writeRepo(curPage,keyWords):
    try:
        keyString='&'.join(keyWords)
        REPOFILE=open('REPOFILE_'+keyString,'a')
        REPOFILE.write('Priority: '+str(curPage['priority'])+'\n')
        REPOFILE.write('Score: '+str(curPage['score'])+'\n')
        REPOFILE.write(curPage.get('data')+'\n')
        REPOFILE.close()

    except IOError:
        print 'Failed to write from pq to File'

