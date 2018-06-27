import requests
import json
import sys
import logging

# used to make Resource Library Requests
class RLreq():
    # static vars
    relationurl = "http://api.ayamel.org/api/v1/relations?_format=json&_key=%s&id=%s"
    resourceurl = "http://api.ayamel.org/api/v1/resources?_format=json&_key=%s&id=%s"

    def __init__(self,key):
        if key == "" or key is None:
            logging.error("No Resource Library key provided.")
        self.key = key

    def get_resources(self, resIds):
        if len(resIds) == 0:
            logging.error("REQUESTED 0 LENGTH RESIDS?!?!?!?!")
            return
        data = self.send_request(resIds)
        resources = self.getResources(data)
        recvd_resource_ids = [res["id"] for res in resources]
        if len(recvd_resource_ids) != len(resIds):
            self.dump_request(resIds, recvd_resource_ids, resources)
        self.resources.extend(resources)

    def get_relations(self, resIds):
        if len(resIds) == 0:
            logging.error("REQUESTED 0 LENGTH RESIDS?!?!?!?!")
            return
        # download the relation
        response_data = self.send_request(resIds, False)
        relations = self.getRelations(response_data)
        # download the resource that corresponds to the relation
        # TODO: add filters on rel["type"] = transcript_of | ...
        relation_resource_ids = [rel["subjectId"] for rel in relations]
        response_data = self.send_request(relation_resource_ids)
        relation_resources = self.getResources(response_data)
        self.relation_resources.extend(relation_resources)

    def send_request(self, resIds, get_res=True):
        base_url = RLreq.resourceurl if get_res else RLreq.relationurl
        url = self.format_url(resIds, base_url)
        response = requests.get(url)
        return json.loads(response.text)

    def format_url(self, rids, base):
        #insert ids separated by commas
        resources = ",".join([r.strip() for r in rids])
        return base % (self.key, resources)

