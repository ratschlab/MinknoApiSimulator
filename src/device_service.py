import config
from prelude import *
from minknow_api import device_pb2, device_pb2_grpc

class DeviceService(device_pb2_grpc.DeviceServiceServicer):
    def get_flow_cell_info(self, request, context):
        info("device: get_flow_cell_info")
        return device_pb2.GetFlowCellInfoResponse(**config.flowcell_info)

    def get_calibration(self, request, context):
        info("device: get_calibration")
        response = device_pb2.GetCalibrationResponse(
            digitisation = config.digitisation,
            has_calibration = config.has_calibration,
        )
        response.offsets.extend([config.offset for _ in range(512)])
        response.pa_ranges.extend([config.pa_range for _ in range(512)])

        return response

    def get_sample_rate(self, request, context):
        info("device: get_sample_rate")
        return device_pb2.GetSampleRateResponse(sample_rate = config.sample_rate)