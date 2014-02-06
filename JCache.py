__author__ = 'admin'

class JCache:
    def __init__(self):
        self.seedsCache={}

    def put(self,key,seeds):
        self.seedsCache[key]=seeds

    def find(self,key):
        return self.seedsCache.get(key)