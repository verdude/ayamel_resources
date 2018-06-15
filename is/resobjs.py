#!/usr/bin/env python
import threading
import requests
import json

# Global list of urls used by threads making requests
RELATIONS = []
RESOURCES = []
NUM_THREADS = 15
relationurl = "http://api.ayamel.org/api/v1/relations?_format=json&limit=10&id="
resourceurl = "http://api.ayamel.org/api/v1/resources?_format=json&limit=10&id="

def isYoutubeLink(url):
    return url.startswith("https://www.youtube.com") or url.startswith("https://youtu.be")

def isVideo(filesObj):
    mime = filesObj["mime"].strip().startswith("video")
    mimeType = filesObj["mimeType"].strip().startswith("video")
    return mime or mimeType

def getResources(d):
    return d["resources"]

def getRelations(d):
    return d["relations"]

class Requester(threading.Thread):
    def __init__(self, src, dst, url, parse):
        self.base_url = url
        self.src = src
        self.parse = parse
        threading.Thread.__init__(self)
    
    def run(self):
        while len(self.src) > 0:
            how_many = 10
            my_content = list()
            
            # Thread safe
            for i in range(how_many):
                try:
                    my_content.append(self.src.pop())
                except:
                    # Encountered empty self.src list... that's fine... finish!
                    break
                    
            url = self.make_url(my_content)
            self.download(url)                

    def download(self, url):
        response = requests.get(url)
        response_dict = json.loads(response.text)
        obj = self.parse(response_dict)
        RESOURCES.extend(obj)
        
    def make_url(self, content_list):
        #insert ids separated by commas

        url = ",".join([ r.strip() for r in content_list ])
        return self.base_url + url

def run_request_process(src, dst, url, parse):
    pool = []
    for i in range(NUM_THREADS): pool.append(Requester(src, dst, url, parse))
    for t in pool: t.start()
    for t in pool: t.join()

content_list = []
with open("resources.txt", "r") as r:
    content_list = r.readlines();

res = content_list
run_request_process(res, RESOURCES, resourceurl, getResources)

with open("brightcove.txt", "w") as bc:
    with open("other.txt", "w") as other:
        with open("youtube.txt", "w") as youtube:
            for x in RESOURCES:
                files = x["content"]["files"][0]
                if "mime" not in files:
                    print("Error: %s" % str(x))
                    continue

                if not isVideo(files):
                    print("Not a video: [%s]" % files["mime"])
                    continue

                url = ""
                if "downloadUri" in files:
                    url = files["downloadUri"]
                if "streamUri" in files:
                    if url != "":
                        print("Overwriting url %s " % url)
                    url = files["streamUri"]
                if files["mime"] == "video/x-brightcove":
                    bc.write(url+"\n")
                elif isYoutubeLink(url):
                    youtube.write(url+"\n")
                else:
                    other.write(url+"\n")

