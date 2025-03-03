from prelude import *
from minknow_api import device_pb2, device_pb2_grpc

class DeviceService(device_pb2_grpc.DeviceServiceServicer):
    def get_flow_cell_info(self, request, context):
        info("device: get_flow_cell_info")
        return device_pb2.GetFlowCellInfoResponse(
            has_flow_cell = True,
            channel_count = 512,
            wells_per_channel = 1,
            flow_cell_id = "f10wc31116",
            asic_id_str = "a51c16-5+r",
            has_adapter = False
        )

    def get_calibration(self, request, context):
        info("device: get_calibration")
        response = device_pb2.GetCalibrationResponse(
            digitisation = 8192,
            has_calibration = True
        )
        response.offsets.extend([384.0 for _ in range(512)])
        response.pa_ranges.extend([936.0 for _ in range(512)])

        return response

    def get_sample_rate(self, request, context):
        info("device: get_sample_rate")
        return device_pb2.GetSampleRateResponse(sample_rate=4000)