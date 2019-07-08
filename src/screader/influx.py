import json
from datetime import datetime

from influxdb import SeriesHelper

from screader import lzstring

lzs = lzstring.LZString()

from influxdb import InfluxDBClient

client = InfluxDBClient('influxdb', 8086, None, None, "screeps")
client.create_database("screeps")


class CPUSeriesHelper(SeriesHelper):
    class Meta:
        client = client
        series_name = 'cpu'
        fields = ['tick', 'cpu', 'limit', 'bucket', 'creeps']
        tags = ['shard']
        bulk_size = 5
        autocommit = True


class VMSeriesHelper(SeriesHelper):
    class Meta:
        client = client
        series_name = 'vm'
        fields = ['tick', 'total_heap_size', 'total_heap_size_executable', 'total_physical_size',
                  'total_available_size',
                  'used_heap_size', 'heap_size_limit', 'malloced_memory', 'peak_malloced_memory',
                  'externally_allocated_size']
        tags = ['shard', ]
        bulk_size = 5
        autocommit = True


def json_hook(a):
    # print(a)
    return dict(a)


def convert(data, index_prefix, min_tick):
    tick = data["t"]
    if tick <= min_tick:
        return None
    time = datetime.utcfromtimestamp(data.get("ti", 0) / 1e3)
    shard = data.get("s", "unknown")
    shard = "leebede"

    CPUSeriesHelper(shard=shard, tick=tick, time=time, cpu=float(data['c']['cpu']), limit=data['c']['limit'],
                    bucket=data['c']['bucket'],
                    creeps=data['crp'])

    del data["vm"]["does_zap_garbage"]
    VMSeriesHelper(shard=shard, tick=tick, time=time, **data["vm"])

    out = []

    for name, process in data['p'].items():
        out.append({
            "_index": f"{index_prefix}process-{shard}-{time.year}-{time.month}-{time.day}",
            "_type": "process",
            "time": time,
            "tick": tick,
            "shard": shard,
            'name': name,
            'cpu_sum': round(process[1], 2),
            'count': process[0],
            'cpu_avg': round(process[1] / process[0], 3)
        })

    for cp in data['cp']:
        out.append({
            "_index": f"{index_prefix}kernel-{shard}-{time.year}-{time.month}-{time.day}",
            "_type": "checkpoint",
            "time": time,
            "tick": tick,
            "shard": shard,
            'idx': cp['id'],
            'cpu': float(cp['cpu']),
            'name': cp['name']
        })

    for annotation in data['a']:
        out.append({
            "_index": f"{index_prefix}annotations-{shard}-{time.year}-{time.month}-{time.day}",
            "_type": "annotation",
            "time": time,
            "tick": tick,
            "shard": shard,
            'text': annotation[0],
            'tags': annotation[1]
        })
    return out


def decode(row, index_prefix, min_tick):
    if len(row) == 0:
        return
    try:
        data = None
        if ord(row[0]) == 7137:
            data = json.loads(lzs.decompressFromUTF16(row), object_pairs_hook=json_hook)
        elif ord(row[0]) == 123:
            data = json.loads(row, object_hook=json_hook)
        else:
            print("UNK", row[0], ord(row[0]), row)
        if data:
            convert(data, index_prefix, min_tick)
    except json.JSONDecodeError:
        pass


def decode_rows(data: str, index_prefix: str, min_tick: int = 0):
    for row in data.split("\n"):
        decode(row, index_prefix, min_tick)

    CPUSeriesHelper.commit()
    VMSeriesHelper.commit()
