import threading
import requests
import json

# Global list of urls used by threads making requests
CONTENT_OBJS = []
RESOURCE_OBJS = []

class Requester(threading.Thread):
    def __init__(self):
        self.base_url = ""
        threading.Thread.__init__(self)
    
    def run(self):
        while len(CONTENT_OBJS) > 0:
            how_many = 100
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
        RESOURCE_OBJS.extend(response_dict["resources"])
        
    def make_url(self, content_list):
        #insert ids separated by commas
        baseUrl = "http://api.ayamel.org/api/v1/resources?_format=json&limit=100&id="

        url = ",".join([ r.resourceId for r in content_list ])
        return baseUrl + url
