import requests
import json
import sys

def get_download_uri(json_obj):
    try:
        content = json_obj["content"]
        return content["files"][0]["downloadUri"].strip()
    except Exception as e:
        print("Error getting downloadUri for resource %s" % str(json_obj))
        return None

class ResLibMetaDl():
    # static vars
    relationurl = "http://api.ayamel.org/api/v1/relations?_format=json&id="
    resourceurl = "http://api.ayamel.org/api/v1/resources?_format=json&id="

    def __init__(self, get_resources=False, get_relations=False,
            resIds=[], read_file=None, write=False, threaded=False, num_threads=0):
        self.write = write
        self.threaded = threaded
        self.num_threads = num_threads
        self.resources = []
        self.relations = []
        self.relation_resources = []
        self.resIds = []

        if read_file is not None:
            with open(read_file, "r") as r:
                self.resIds = r.readlines();
        else:
            print("We need the resource file ")
            return
        if get_resources:
            self.get_resources()
        if get_relations:
            for i in range(0,len(resIds),20):
                self.download_relations(resIds[i:20])
            if write:
                self.write_relations()

    def get_resources(self):
        if len(self.resIds) == 0:
            print("Need resourceIDs first")
            return
        for i in range(0,len(self.resIds),20):
            self.download_resources(self.resIds[i:20])

    def get_relations(self):
        if len(self.resIds) == 0:
            print("Need resourceIDs first")
            return
        for i in range(0,len(self.resIds),20):
            self.download_relations(self.resIds[i:20])

    def download_resources(self, resIds):
        data = self.send_request(resIds)
        resources = self.getResources(data)
        self.resources.extend(resources)

    def download_relations(self, resIds):
        # download the relation
        response_data = self.send_request(resIds, False)
        relations = self.getRelations(response_data)
        self.relations.extend(relations)
        # filter out duplicates in the list of dictionaries
        self.relations = list({v["id"]:v for v in self.relations}.values())
        # download the resource that corresponds to the relation
        # TODO: add filters on rel["type"] = transcript_of | ...
        relation_resource_ids = [rel["subjectId"] for rel in relations]
        response_data = self.send_request(relation_resource_ids)
        relation_resources = self.getResources(response_data)
        self.relation_resources.extend(relation_resources)

    def change_relation_names(self):
        # this function looks throught the relations that already have been downloaded
        # and matches them with the resource objects and names them after their related resources
        diff = len(self.relations) - len(self.relation_resources)
        if len(self.resources) == 0:
            self.get_resources()
        if len(self.relations) == 0:
            self.get_relations()
        if diff != 0:
            diff = "more" if diff > 0 else "less"
            print("There are %s relations than there are relation_resources!" % diff)
            return
        rels = []
        for i,rel in enumerate(self.relations):
            for obj in self.resources:
                if obj["id"] == rel["objectId"]:
                    res = obj
                    break
            for sub in self.relation_resources:
                if sub["id"] == rel["subjectId"]:
                    dl = get_download_uri(sub)
                    if dl is None:
                        print("Failed on %i", i)
                        return
                    ext = dl.split(".")[-1]
                    rels.append("%s::%s_%s.%s" % (dl, obj["title"], sub["title"], ext))
                    break
        return rels
            
    def write_relation_urls(self):
        if len(self.relation_resources) == 0:
            print("No Relation resources found. Not writing urls to file...")
            return
        downloadUris = [get_download_uri(r) for r in self.relation_resources]
        with open("document_urls.txt", "w") as docs:
            docs.writelines(downloadUris)

    def download_relation_documents(self):
        downloadUris = [get_download_uri(r) for r in self.relation_resources]


    def send_request(self, resIds, get_res=True):
        base_url = ResLibMetaDl.resourceurl if get_res else ResLibMetaDl.relationurl
        url = self.format_url(resIds, base_url)
        response = requests.get(url)
        return json.loads(response.text)

    def format_url(self, rids, base):
        #insert ids separated by commas
        resources = ",".join([r.strip() for r in rids])
        return base + resources

    def isYoutubeLink(self, url):
        return url.startswith("https://www.youtube.com") or url.startswith("https://youtu.be")

    def isVideo(self, filesObj):
        mime = filesObj["mime"].strip().startswith("video")
        mimeType = filesObj["mimeType"].strip().startswith("video")
        return mime or mimeType

    def getResources(self, d):
        return d["resources"]

    def getRelations(self, d):
        return d["relations"]

    def write_relations(self):
        with open("relation_resources.txt", "w") as rel:
            rel.write(json.dumps(self.relation_resources))

    def save_to_file(self):
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

