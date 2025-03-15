
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

break_reads_after_seconds = .4

flowcell_info = {
            'has_flow_cell': True,
            'channel_count': 512,
            'wells_per_channel': 1,
            'flow_cell_id': "f10wc31116",
            'asic_id_str': "a51c16-5+r",
            'has_adapter': False
}

digitisation = 8192
has_calibration = True
offset = 384.0
pa_range = 936.0

sample_rate = 4000  #