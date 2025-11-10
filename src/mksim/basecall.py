from datetime import datetime
from time import sleep
import argparse
import numpy as np

# dorado v7.4
# from pybasecall_client_lib.pyclient import PyBasecallClient as pclient
# from pybasecall_client_lib.helper_functions import basecall_with_pybasecall_client, package_read

# dorado v7.2
from pyguppy_client_lib.pyclient import PyGuppyClient as pclient
from pyguppy_client_lib.helper_functions import package_read

#guppy

import read5

BATCH_SZ = 1024

def calibration(digitisation, range):
    """
    input:
        digitisation: float
        range: float
    output:
        scale: float
    """
    return range / digitisation

def pass_reads_batch(reads: list, client: pclient):
    n_tries = 10
    while n_tries > 0:
        res = client.pass_reads(reads)
        if res:
            break
        else:
            n_tries -= 1
            sleep(.1)
    if n_tries == 0:
        raise RuntimeError("Could not send read batch")


def pass_reads(reads: list, client: pclient):
    for read in reads:
        n_tries = 10
        while n_tries > 0:
            res = client.pass_read(read)
            if res:
                break
            else:
                n_tries -= 1
                sleep(.1)
        if n_tries == 0:
            raise RuntimeError("Could not send read")
        print('.', end='')


def main(signal_in, fasta_out, config, address):
    client = pclient(address=address, config=config)
    client.connect()
    print(client.get_protocol_version())
    print(client.get_software_version())

    r5 = read5.read(signal_in)
    out = open(fasta_out, 'w')

    requests = []
    i = 0
    n_sent = 0
    last_status_update = datetime.now()
    try:
        for readid in r5:
            req = {
                'read_tag': i,
                'read_id': readid,
                'raw_data': np.ndarray.copy(r5.getSignal(readid)),
                'daq_offset': r5.getOffset(readid),
                'daq_scaling': r5.getCalibrationScale(readid)
            }
            # req = package_read(
            #     read_id=readid,
            #     raw_data=r5.getSignal(readid),
            #     daq_offset=r5.getOffset(readid),
            #     daq_scaling=r5.getCalibrationScale(readid),
            #     sampling_rate=4000,
            #     start_time=i,
            #     read_tag=i,
            # )
            requests.append(req)
            i += 1
            n_sent += 1
            if n_sent == BATCH_SZ:
                pass_reads_batch(requests, client)
                requests.clear()

                while n_sent > 0:
                    called = client.get_completed_reads()
                    if not called:
                        sleep(.1)
                    else:
                        for calls in called:
                            for call in calls:
                                try:
                                    read_id = call['metadata']['read_id']
                                    sequence = call['datasets']['sequence']
                                    out.write('>' + read_id + '\n' + sequence + '\n')
                                    n_sent -= 1
                                except Exception as error:
                                    print("An exception occurred in stage 1:", type(error).__name__, "-", error)
                if (datetime.now() - last_status_update).total_seconds() > 5:
                    print('%d reads processed' % i)
                    last_status_update = datetime.now()
    finally:
        out.close()
    print('%d reads processed' % i)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("signal_in", type=str, help="Signal file (fast5/pod5/slow5/blow5)")
    parser.add_argument("fasta_out", type=str, help="Output fasta file")
    parser.add_argument("-c", "--config", type=str, default="dna_r9.4.1_450bps_fast",
                        help="Configuration file [default: dna_r9.4.1_450bps_fast]")
    parser.add_argument('-a', '--address', type=str, default='ipc:///tmp/.guppy/5555',
                        help='address of dorado server, [default: ipc:///tmp/.guppy/5555]')

    args = parser.parse_args()
    print(args)
    main(args.signal_in, args.fasta_out, args.config, args.address)