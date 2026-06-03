import argparse
from dataclasses import dataclass, fields
from typing import List
import threading

stop_event = threading.Event()

# Obtained the following values from seq2squiggle
profiles = {
    "dna-r10-min": {
        "digitisation": 8192,
        "sample_rate": 5000,
        "bps": 400,
        "range": 1536.598389,
        "offset_mean": 13.380569389019,
        "offset_std": 16.311471649012,
        "median_before_mean": 202.15407438804,
        "median_before_std": 13.406139241768,
    },
    "dna-r10-prom": {
        "digitisation": 2048,
        "sample_rate": 5000,
        "bps": 400,
        "range": 281.345551,
        "offset_mean": -127.5655735,
        "offset_std": 19.377283387665,
        "median_before_mean": 189.87607393756,
        "median_before_std": 15.788097978713,
    },
    "dna-r9-min": {
        "digitisation": 8192,
        "sample_rate": 4000,
        "bps": 450,
        "range": 1443.030273,
        "offset_mean": 13.7222605,
        "offset_std": 10.25279688,
        "median_before_mean": 200.815801,
        "median_before_std": 20.48933762,
    },
    "dna-r9-prom": {
        "digitisation": 2048,
        "sample_rate": 4000,
        "bps": 450,
        "range": 748.5801,
        "offset_mean": -237.4102,
        "offset_std": 14.1575,
        "median_before_mean": 214.2890337,
        "median_before_std": 18.0127916,
    },
    "rna-004-min": {
        "digitisation": 8192,
        "sample_rate": 4000,
        "bps": 130,
        "range": 1437.976685,
        "offset_mean": 12.47686423863,
        "offset_std": 10.442126577137,
        "median_before_mean": 205.08496731088,
        "median_before_std": 8.6671292866233,
    },
    "rna-004-prom": {
        "digitisation": 2048,
        "sample_rate": 4000,
        "bps": 130,
        "range": 299.432068,
        "offset_mean": -259.421128,
        "offset_std": 16.010841823643,
        "median_before_mean": 189.87607393756,
        "median_before_std": 15.788097978713,
    },
}

def get_digitisation(profile_name):
    return profiles[profile_name]['digitisation']

def get_offset_mean(profile_name):
    return profiles[profile_name]['offset_mean']

def get_range(profile_name):
    return profiles[profile_name]['range']

def get_sample_rate(profile_name):
    return profiles[profile_name]['sample_rate']


@dataclass
class Params:
    input: List[str]
    certs: str
    profile: str
    name: str = 'MN12345'
    port: int = 50051
    channel_count: int = 512
    chunk_time: float = 0.4
    run_id: str = 'test_run'
    output_path: str = "/tmp/MinknoApiSimulator/out"
    wait_seconds: int = 10
    occupancy: float = 1.0
    benchmark_chunks: int = 0

params = None

read_classifications = {
                83: "strand",
                67: "strand1",
                82: "strand2", # fixme
                81: "short_strand", # fixme
                79: "unknown_positive", # fixme
                77: "multiple",
                90: "zero",
                65: "adapter",
                66: "mux_uncertain",
                70: "user2",
                68: "user1",
                69: "event",
                80: "pore",
                85: "unavailable",
                84: "transition",
                78: "unclassed"
            }

flowcell_info_partial = {
            'has_flow_cell': True,
            'channel_count': -1,
            'wells_per_channel': 1,
            'flow_cell_id': "f10wc31116",
            'asic_id_str': "a51c16-5+r",
            'has_adapter': False
}

minknow_version_info = {'major':6, 'minor':0, 'patch':0, 'full':"6.0.0"}

other_version_info = {
            'bream':"4.5.6",
            'distribution_version':"6.0.0",
            'protocol_configuration':"a.b.c",
            'basecaller_build_version':"7.4.12+0e5e75c49",
            'basecaller_connected_version':"7.4.12+0e5e75c49"
}

def get_params() -> None:
    parser = argparse.ArgumentParser(description="Minknow server simulator")

    # Automatically add arguments based on the Config dataclass fields
    for field in fields(Params):
        field_type = field.type

        # For fields that are required, explicitly set 'required=True'
        if field.default is field.default_factory:  # Check if default is absent
            is_required = True
        else:
            is_required = False

        if field_type == List[str]:
            # For List fields, handle them as an optional list of values
            parser.add_argument(
                f'--{field.name}',
                action='append',  # Accepts multiple values
                required=is_required,  # Only set required if field has no default
                help=f"List of {field.name} values"
            )
        elif field_type == bool:
            # Boolean flags, no value expected
            parser.add_argument(
                f'--{field.name}',
                action='store_true',  # Presence means True
                required=is_required,  # Only set required if field has no default
                help=f"Set {field.name} to True"
            )
        else:
            # For other types, handle with default or required flag
            parser.add_argument(
                f'--{field.name}',
                type=field_type,
                default=getattr(Params, field.name, None),  # Use None if no default
                required=is_required,  # Only set required if field has no default
                help=f"Set the {field.name} (default: {getattr(Params, field.name, None)})"
            )

    parsed_args = parser.parse_args()
    global params
    params = Params(**vars(parsed_args))

if __name__ == '__main__':
    get_params()
    print(vars(params))