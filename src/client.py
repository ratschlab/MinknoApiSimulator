import grpc

from minknow_api import data_pb2, Connection
from minknow_api.data import get_numpy_types
import numpy as np


def generate_setup_stream():
    yield data_pb2.GetLiveReadsRequest(
        setup=data_pb2.GetLiveReadsRequest.StreamSetup(
            first_channel=1,
            last_channel=512,
            raw_data_type=data_pb2.GetLiveReadsRequest.RawDataType.UNCALIBRATED,
            sample_minimum_chunk_size=0,
        )
    )

def pretty_print(channel, read):
    data = np.frombuffer(read.raw_data, dtype=np.int16)
    rid = read.id
    slen = len(data)
    front = str(data[:10])
    back = str(data[-10:])
    print("[{}] = {}: [{}...{}] ({})".format(channel, rid, front, back, slen))

def main():
    connection = Connection(host="localhost", port=50051)
    setup_request = generate_setup_stream()

    reads = connection.data.get_live_reads(setup_request)
    for reads_chunk in reads:
        for read_channel in reads_chunk.channels:
            read = reads_chunk.channels[read_channel]
            pretty_print(read_channel, read)


if __name__ == "__main__":
    main()

