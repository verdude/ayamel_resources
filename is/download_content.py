from resourcelibrarymetadatadownloader import ResLibMetaDl

if __name__ == "__main__":
    rlmdl = ResLibMetaDl(read_file="resources.txt",
            get_resources=True, get_relations=True, write=False)
    documents = rlmdl.change_relation_names()
    annotations = [x+"\n" for x in documents if x.endswith("json")]
    subtitles = [x+"\n" for x in documents if not x.endswith("json")]
    with open("subtitles.txt", "w") as subs:
        subs.writelines(subtitles)
    with open("annotations.txt", "w") as subs:
        subs.writelines(annotations)

