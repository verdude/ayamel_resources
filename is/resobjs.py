#!/usr/bin/env python
import threading
import requests
import json

# Global list of urls used by threads making requests
CONTENT_OBJS = []
RELATIONS = []
RESOURCE_OBJS = []
NUM_THREADS = 15
relationurl = "http://api.ayamel.org/api/v1/relations?_format=json&limit=10&id="
resourceurl = "http://api.ayamel.org/api/v1/resources?_format=json&limit=10&id="

def getResources(d):
    return d["resources"]

def getRelations(d):
    return d["relations"]

class Requester(threading.Thread):
    def __init__(self, url, src, dst, handle):
        self.base_url = url
        self.dst = dst
        self.handle = handle
        threading.Thread.__init__(self)
    
    def run(self):
        while len(CONTENT_OBJS) > 0:
            how_many = 10
            my_content = list()
            
            # Thread safe
            for i in range(how_many):
                try:
                    my_content.append(CONTENT_OBJS.pop())
                except:
                    # Encountered empty CONTENT_OBJS list... that's fine... finish!
                    break
                    
            url = self.make_url(my_content)
            self.download(url)                

    def download(self, url):
        response = requests.get(url)
        response_dict = json.loads(response.text)
        obj = self.handle(response_dict)
        self.dst.extend(obj)
        
    def make_url(self, content_list):
        #insert ids separated by commas

        url = ",".join([ r.strip() for r in content_list ])
        return self.base_url + url

def run_request_process(src, dst, url, handle):
    pool = []
    for i in range(NUM_THREADS): pool.append(Requester(url, src, dst, handle))
    for t in pool: t.start()
    for t in pool: t.join()

content_list = []
with open("resources.txt", "r") as r:
    content_list = r.readlines();

CONTENT_OBJS.extend(content_list)
run_request_process(CONTENT_OBJS, RESOURCE_OBJS, resourceurl, getResources)

