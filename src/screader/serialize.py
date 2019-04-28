import json
from datetime import datetime

from screader import lzstring

lzs = lzstring.LZString()


def json_hook(a):
    # print(a)
    return dict(a)


def convert(data, min_tick):
    tick = data["t"]
    if tick <= min_tick:
        return None
    shard = data.get("s", "")
    time = datetime.utcfromtimestamp(data.get("ti", 0) / 1e3)
    out = [{
        "_index": f"cpu-{shard}-{time.year}-{time.month}-{time.day}",
        "_type": "cpu",
        "time": time,
        "tick": tick,
        "shard": shard,
        "cpu": {
            "cpu": float(data['c']['cpu']),
            "limit": data['c']['limit'],
            "bucket": data['c']['bucket'],
        },
        "heap": data['vm']
    }]

    return out


def decode(row, min_tick):
    if len(row) == 0:
        return []
    try:
        data = None
        if ord(row[0]) == 7137:
            data = json.loads(lzs.decompressFromUTF16(row), object_pairs_hook=json_hook)
        elif ord(row[0]) == 123:
            data = json.loads(row, object_hook=json_hook)
        else:
            print("UNK", row[0], ord(row[0]), row)
        if data:
            return convert(data, min_tick)
    except json.JSONDecodeError:
        return []


def decode_rows(data: str, min_tick: int = 0):
    for row in data.split("\n"):
        data = decode(row, min_tick)
        if data is not None:
            for msg in data:
                yield msg
        else:
            return
