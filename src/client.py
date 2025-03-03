import grpc

from minknow_api import data_pb2, Connection
from minknow_api.data import get_numpy_types


def generate_setup_stream():
    yield data_pb2.GetLiveReadsRequest(
        setup=data_pb2.GetLiveReadsRequest.StreamSetup(
            first_channel=1,
            last_channel=512,
            raw_data_type=data_pb2.GetLiveReadsRequest.RawDataType.UNCALIBRATED,
            sample_minimum_chunk_size=0,
        )
    )

def main():
    connection = Connection(host="localhost", port=50051)
    setup_request = generate_setup_stream()

    reads = connection.data.get_live_reads(setup_request)
    for reads_chunk in reads:
        for read_channel in reads_chunk.channels:
            read = reads_chunk.channels[read_channel]
            print(read)


if __name__ == "__main__":
    main()

