import os
from time import sleep

import urllib3
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Search

from screader.serialize import decode_rows
from screader.tools import get_segment

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es = Elasticsearch([os.environ['ES_HOST']],
                   http_auth=(os.environ['ES_USERNAME'], os.environ['ES_PASSWORD']),
                   scheme="https",
                   verify_certs=False)


def update_data():
    tick = get_last_tick()
    print(tick)
    segment = get_segment(9).get("data")
    bulk(es, decode_rows(segment, min_tick=tick))


def get_latest_record():
    s = Search(using=es, index="cpu-*").sort("-tick")[1]
    r = s.execute()
    if len(r.hits):
        return r.hits[0]


def get_last_tick():
    tick = get_latest_record()
    if tick:
        return tick.tick
    return 0


def main():
    while 1:
        update_data()
        sleep(10)


if __name__ == "__main__":
    main()
