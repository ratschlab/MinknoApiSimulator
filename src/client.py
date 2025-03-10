import grpc

from minknow_api import data_pb2, Connection
from minknow_api.data import get_numpy_types
import numpy as np
import time
import queue

from test_utils import *

def pretty_print(channel, read):
    data = np.frombuffer(read.raw_data, dtype=np.int16)
    rid = read.id
    slen = len(data)
    front = str(data[:10])
    back = str(data[-10:])
    print("[{}] = {}: [{}...{}] ({})".format(channel, rid, front, back, slen))


def generate_setup_stream():
    yield data_pb2.GetLiveReadsRequest(
        setup=data_pb2.GetLiveReadsRequest.StreamSetup(
            first_channel=1,
            last_channel=512,
            raw_data_type=data_pb2.GetLiveReadsRequest.RawDataType.UNCALIBRATED,
            sample_minimum_chunk_size=0,
        )
    )

def generate_requests(req_queue: queue.Queue):
    yield data_pb2.GetLiveReadsRequest(
        setup=data_pb2.GetLiveReadsRequest.StreamSetup(
            first_channel=1,
            last_channel=512,
            raw_data_type=data_pb2.GetLiveReadsRequest.RawDataType.UNCALIBRATED,
            sample_minimum_chunk_size=0,
        )
    )

    while True:
        while not req_queue.empty():
            action_group = req_queue.get()
            yield data_pb2.GetLiveReadsRequest(
                actions=data_pb2.GetLiveReadsRequest.Actions(actions=action_group)
            )


def print_all(connection: Connection):
    setup_request = generate_setup_stream()
    reads = connection.data.get_live_reads(setup_request)
    while True:
        for reads_chunk in reads:
            for read_channel in reads_chunk.channels:
                read = reads_chunk.channels[read_channel]
                pretty_print(read_channel, read)
        time.sleep(1)


def unblock_all(connection: Connection):
    req_queue = queue.Queue()
    generator = generate_requests(req_queue)
    reads = connection.data.get_live_reads(generator)
    for reads_chunk in reads:
        blurt("A%d-D%d" % (len(reads_chunk.action_responses), len(reads_chunk.channels)), color=MAG)
        actions = [
            data_pb2.GetLiveReadsRequest.Action(
                action_id="unblock_" + read.id,
                channel=channel,
                id=read.id
            )
            for channel, read in reads_chunk.channels.items()
        ]
        req_queue.put(actions)


def main():
    connection = Connection(host="localhost", port=50051)
    unblock_all(connection)


if __name__ == "__main__":
    main()

