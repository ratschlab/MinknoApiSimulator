import argparse
from dataclasses import dataclass, fields
from typing import List

@dataclass
class Params:
    input: str
    name: str = 'MN12345'
    port: int = 50051
    channel_count: int = 512
    sample_rate: int = 4000
    chunk_time: float = 0.4
    digitisation: int = 8192
    offset: float = 384.0
    pa_range: float = 936.0
    run_id: str = 'test_run'
    output_path: str = "/tmp/MinknoApiSimulator/out"
    wait_seconds: int = 10


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
                type=str,
                nargs='+',  # Accepts multiple values
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