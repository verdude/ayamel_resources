import requests
import logging
import sys
import getpass
import json
import argparse

BC_LINKS = "brightcove_download_links.txt"

def get_links():
    links = []
    with open("brightcove.txt", "r") as bc:
        links = bc.readlines()
    with open("youtube.txt", "r") as youtube:
        links.extend(youtube.readlines())
    with open("other.txt", "r") as other:
        links.extend(other.readlines())
    return links

def wrap_up(completed, last, num):
    print("Got %i download links." % num)
    if completed:
        print("Finished. Download links saved to file: %s" % BC_LINKS)
    else:
        print("Stopped at %s." % last)
        print("Exited with errors.")

def bc_video_ids(links):
    return [link.split("//")[1].strip() for link in links if link.startswith("brightcove")]

def get_brightcove_dl_links(video_ids, EMAIL, PASSWORD, account_id, token, offset):
    video_ids = video_ids[offset:]
    if offset > 0:
        logging.info("Starting at offset %i. Brightcove Id: %s" % (offset, video_ids[0]))
    if len(video_ids) == 0:
        logging.error("No video_ids provided")
        sys.exit(1)
    base_url = "https://cms.api.brightcove.com/v1/accounts/%s/videos/%s/sources"
    token = token.strip().split(" ")[-1]
    headers = {"Authorization": "Bearer %s" % token}
    dl_links = []
    for i,video_id in enumerate(video_ids):
        response = requests.get(base_url % (account_id, video_id), headers=headers)

        if response.status_code != 302 and response.status_code != 200:
            logging.info("Response returned %i" % response.status_code)
            js = json.loads(response.text)
            if "error_code" in js[0] and js[0]["error_code"] == "UNAUTHORIZED":
                print("Token Expired on: %s" % video_id)
                wrap_up(False, video_id, i)
                return dl_links
        else:
            sources = json.loads(response.text)
            sources = list(filter(lambda x: x["container"] == "MP4", sources))
            if len(sources) == 0:
                logging.info("No MP4 Sources for %s" % video_id)
                logging.debug(response.text)
                continue
            source = max(sources, key=lambda x:x["width"])
            dl_links.append(source["src"] + "\n")
            logging.debug("Source: %s" % str(source))
            logging.info("Got URL for %s" % video_id)

    wrap_up(True, video_ids[-1], len(dl_links))
    return dl_links

def get_brightcove_email_password():
    EMAIL = input("Enter Brightcove Email: ")
    PASSWORD = getpass.getpass(prompt="Enter Brightcove Password: ")
    return (EMAIL, PASSWORD)

def download_videos(offset):
    with open("creds.txt", "r") as creds:
        js = json.load(creds)
        email = js["email"]
        password = js["password"]
        account_id = js["account_id"]
        token = js["token"]

    links = get_links()
    bc_dl_links = get_brightcove_dl_links(bc_video_ids(links), email, password, account_id, token, offset)
    if offset > 0:
        write_mode = "w+"
    else:
        write_mode = "w"
    with open(BC_LINKS, write_mode) as bcdl:
        bcdl.writelines(bc_dl_links)

def parse_options():
    parser = argparse.ArgumentParser(prog="updates", description="Send Text", add_help=True)

    parser.add_argument("-o", "--offset", action="store", type=int, help="Start at the given Resource number")
    parser.add_argument("-d", "--debug", action="store_true", help="set logging to debug")
    parser.add_argument("-q", "--quiet", action="store_true", help="set logging to quiet")
    return parser.parse_args()

def config_logging(args):
    if args.quiet:
        lg_level = logging.WARN
    elif args.debug:
        lg_level = logging.DEBUG
    else:
        lg_level = logging.INFO
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.basicConfig(level=lg_level)


args = parse_options()
config_logging(args)
download_videos(args.offset if args.offset else 0)

