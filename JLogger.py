__author__ = 'admin'
from JColors import JColors

def log(message):
        print message
        try:
            LOGFILE=open('LOGFILE','a')
            LOGFILE.write(message+'\n')
            LOGFILE.close()
        except IOError:
            print JColors.FAIL+'Failed to open log file!\n'