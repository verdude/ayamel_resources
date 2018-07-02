import requests
import json
import sys
import logging
from resourcedl import RLreq

def get_download_uri(json_obj):
    try:
        content = json_obj["content"]
        return content["files"][0]["downloadUri"].strip()
    except Exception as e:
        logging.error("Error getting downloadUri for resource %s" % str(json_obj))
        return None

def get_key(filename=None):
    with open("creds.txt" if not filename else filename, "r") as creds:
        js = json.load(creds)
    k = js["resourcelibrarykey"]
    if k == "":
        logging.error("Resource Library key is empty.")
    return k

class ResLibMetaDl():

    def __init__(self, get_resources=False, get_relations=False,
            resIds=[], read_file=None, write=False, threaded=False, num_threads=0):
        self.write = write
        self.threaded = threaded
        self.num_threads = num_threads
        self.resources = []
        self.relations = []
        self.relation_resources = []
        self.resIds = []
        self.key = get_key()
        self.rlr = RLreq(self.key)

        if read_file is not None:
            with open(read_file, "r") as r:
                # get unique list of resources from file
                self.resIds = list(set([res.strip() for res in r.readlines()]))
        else:
            logging.error("We need the resource file ")
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
            logging.error("Need resourceIDs first")
            return
        for i in range(0,len(self.resIds),20):
            self.download_resources(self.resIds[i:20])

    def get_relations(self):
        if len(self.resIds) == 0:
            logging.error("Need resourceIDs first")
            return
        for i in range(0,len(self.resIds),20):
            self.download_relations(self.resIds[i:20])

    def dump_request(self, reqid, recvid, recv):
        logging.error("Recieved incorrect amount of resources.")
        with open("req_id_dump.txt", "w") as req_d:
            req_d.writelines("\n".join(reqid))
        with open("recv_id_dump.txt", "w") as recv_d:
            recv_d.writelines("\n".join(list(recvid)))
        with open("recv_data_dump.txt", "w") as data_d:
            data_d.write(json.dumps(recv))
        logging.info("Wrote dump files.")
        sys.exit(1)

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
            logging.warning("There are %s relations than there are relation_resources!" % diff)
            return
        rels = []
        for rel in self.relations:
            res = None
            ext = None
            for obj in self.resources:
                if obj["id"] == rel["objectId"]:
                    res = obj
                    break
            for sub in self.relation_resources:
                if sub["id"] == rel["subjectId"]:
                    if res is None:
                        logging.error("Resource not found for %s" % rel["objectId"])
                        logging.debug(sub)
                        logging.debug(rel)
                        logging.debug(self.relations.index(rel))
                        return
                    dl = get_download_uri(sub)
                    if dl is None:
                        logging.error("Failed on %i", i)
                        return
                    ext = dl.split(".")[-1]
                    rels.append("%s::%s_%s.%s" % (dl, res["title"], sub["title"], ext))
                    break
        return rels
            
    def write_relation_urls(self):
        if len(self.relation_resources) == 0:
            logging.error("No Relation resources found. Not writing urls to file...")
            return
        downloadUris = [get_download_uri(r) for r in self.relation_resources]
        with open("document_urls.txt", "w") as docs:
            docs.writelines(downloadUris)

    def download_relation_documents(self):
        downloadUris = [get_download_uri(r) for r in self.relation_resources]

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
                    for x in self.resources:
                        if "content" not in x:
                            continue
                        files = x["content"]["files"][0]
                        if "mime" not in files:
                            logging.error("%s" % str(x))
                            continue

                        if not self.isVideo(files):
                            logging.error("Not a video: [%s]" % files["mime"])
                            continue

                        url = ""
                        if "downloadUri" in files:
                            url = files["downloadUri"]
                        if "streamUri" in files:
                            if url != "":
                                logging.warning("Overwriting url %s " % url)
                            url = files["streamUri"]
                        if files["mime"] == "video/x-brightcove":
                            bc.write(url+"\n")
                        elif self.isYoutubeLink(url):
                            youtube.write(url+"\n")
                        else:
                            other.write(url+"\n")

