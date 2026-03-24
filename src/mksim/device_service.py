from . import config
from minknow_api import device_pb2, device_pb2_grpc

class DeviceService(device_pb2_grpc.DeviceServiceServicer):
    def get_flow_cell_info(self, request, context):
        flowcell_info = config.flowcell_info_partial
        flowcell_info['channel_count'] = config.params.channel_count
        return device_pb2.GetFlowCellInfoResponse(**flowcell_info)

    def get_calibration(self, request, context):
        response = device_pb2.GetCalibrationResponse(
            digitisation = config.get_digitisation(config.params.profile),
            has_calibration = True,
        )
        response.offsets.extend([ config.get_offset_mean(config.params.profile) for _ in range(512)])
        response.pa_ranges.extend([config.get_range(config.params.profile) for _ in range(512)])
        return response

    def get_sample_rate(self, request, context):
        return device_pb2.GetSampleRateResponse(sample_rate = config.get_sample_rate(config.params.profile))