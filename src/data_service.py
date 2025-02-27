from prelude import *
from minknow_api import data_pb2, data_pb2_grpc

class DataService(data_pb2_grpc.DataServiceServicer):
    def __init__(self):
        self.setup_config = None

    def get_data_types(self, request, context):
        info("data: get_data_types")
        return data_pb2.GetDataTypesResponse(
            uncalibrated_signal = data_pb2.GetDataTypesResponse.DataType(
                type=data_pb2.GetDataTypesResponse.DataType.Type.SIGNED_INTEGER, big_endian=False, size=2
            ),
            calibrated_signal = data_pb2.GetDataTypesResponse.DataType(
                type=data_pb2.GetDataTypesResponse.DataType.Type.FLOATING_POINT, big_endian=False, size=4
            ),
            bias_voltages = data_pb2.GetDataTypesResponse.DataType(
                type=data_pb2.GetDataTypesResponse.DataType.Type.SIGNED_INTEGER, big_endian=False, size=2
            )
        )

    def get_live_reads(self, request_iterator, context):
        info("data: get_live_reads")
        # Handle incoming requests from the client
        for request in request_iterator:
            if request.HasField("setup"):
                # Handle StreamSetup request -- todo
                print(f"Received StreamSetup: first_channel={request.setup.first_channel}, "
                      f"last_channel={request.setup.last_channel}, "
                      f"raw_data_type={request.setup.raw_data_type}")
                # You can store the setup configuration for later use
                self.setup_config = request.setup

            elif request.HasField("actions"):
                # Handle Actions request
                for action in request.actions.actions:
                    print(f"Received Action: action_id={action.action_id}, "
                          f"channel={action.channel}, read_id={action.id}")
                    # Simulate processing the action -- todo
                    action_response = data_pb2.GetLiveReadsResponse.ActionResponse(
                        action_id=action.action_id,
                        response=data_pb2.GetLiveReadsResponse.ActionResponse.Response.SUCCESS
                    )
                    yield data_pb2.GetLiveReadsResponse(
                        action_responses=[action_response]
                    )

            if self.setup_config is not None:
                # Simulate sending live reads to the client
                read_data = data_pb2.GetLiveReadsResponse.ReadData(
                    id="read_123",
                    start_sample=1000,
                    chunk_start_sample=1000,
                    chunk_length=200,
                    chunk_classifications=[1, 2, 3],
                    raw_data=b"raw_data_bytes",
                    median_before=50.0,
                    median=55.0,
                    previous_read_classification=1,
                    previous_read_end_reason=data_pb2.statistics.ReadEndReason.UNBLOCK
                )
                yield data_pb2.GetLiveReadsResponse(
                    samples_since_start=1000,
                    seconds_since_start=10.0,
                    channels={
                        1: read_data
                    }
                )
            else:
                yield data_pb2.GetLiveReadsResponse(
                    samples_since_start=0,
                    seconds_since_start=0.0,
                    channels={}
                )


