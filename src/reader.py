import sys
from itertools import count
from minknow_api import data_pb2, data_pb2_grpc

from read5 import read
from test_utils import *
import zmq
import time
from multiprocessing import Process
from dataclasses import dataclass
from prelude import *

blow5_file = "/scratch/Zymo/signal/blow5/s180/0/Sigs-0.blow5"
fast5_file = "/scratch/Zymo/signal/fast5/s180/0/Sigs-0.fast5"
pod5_file = "/data/PBA70346_skip_5c03b04e_00bcc91b_0.pod5"

CHUNK_SIZE = 1600

def test_read(filename):
    r5 = read(filename)
    for i in range(5):
        readid = next(r5)
        signal = r5.getSignal(readid)
        pA_signal = r5.getpASignal(readid)
        print("Read-id:", readid)
        print_vectors(signal=signal, pA_signal=pA_signal)

    # count = 0
    # for readid in r5:
    #     signal = r5.getSignal(readid)  # returns raw integer values stored in the file
    #     pA_signal = r5.getpASignal(readid)  # returns pA signal
    #     # channel = r5.getChannelNumber(readid)
    #     # sampleid = r5.getSampleID(readid)
    #     # runid = r5.getRunID(readid)
    #
    #     # print("Channel:", channel)
    #     # print("SampleID:", sampleid)
    #     # print("RunID:", runid)
    #     print("Read-id:", readid)
    #     print_vectors(signal=signal, pA_signal=pA_signal)
    #
    #     count = count + 1
    #     if count == 5: break

@dataclass
class Read:
    def __init__(self, rid, signal):
        self.rid = rid
        self.signal = signal

def package_read(read: Read, start: int):
    length = min(CHUNK_SIZE, len(read.signal) - start)
    return data_pb2.GetLiveReadsResponse.ReadData(
        id=read.rid,
        chunk_classifications=[83], # strand
        chunk_length=length,
        raw_data=read.signal[start:start + length],
    )


class ReadDataThreads:
    def __init__(self, filename, n_channels):
        self.r5 = read(filename)
        self.n_channels = n_channels
        self.reads = [None for _ in range(n_channels)]
        self.offsets = [0 for _ in range(n_channels)]
        self.stop_receiving = set()
        self.eject = set

    def _update(self):
        for i in range(self.n_channels):
            if self.reads[i] is not None:
                advance = min(CHUNK_SIZE, len(self.reads[i].signal) - self.offsets[i])
                self.offsets[i] += advance
            if self.reads[i] is None or len(self.reads[i].signal) == self.offsets[i]:
                rid = next(self.r5)
                if rid is not None:
                    self.reads[i] = Read(rid, self.r5.getSignal(rid))
                    self.offsets[i] = 0
                else:
                    self.reads[i] = None
                    self.offsets[i] = 0

    def _eject(self, i):
        self.reads[i] = None

    def get_data(self):
        data = {}
        self._update()
        for i in range(self.n_channels):
            if i in self.stop_receiving:
                continue # don't add the read to the result
            elif i in self.eject:
                self._eject(i)
            elif self.reads[i] is not None:
                data[i] = package_read(self.reads[i], self.offsets[i])
        return data

def server(filename=blow5_file, n_channels=512):
    info("Initializing reader..")
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("ipc:///tmp/mksim")

    read_data_threads = ReadDataThreads(filename, n_channels)
    last_sampled = time.time()

    while True:
        #  Wait for next request from client
        message = socket.recv()
        data = read_data_threads.get_data()
        current_time = time.time()
        elapsed_time = current_time - last_sampled
        if elapsed_time < 0.4: time.sleep(0.4 - elapsed_time)
        socket.send_pyobj(data)

def client():
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to hello world server...")
    socket = context.socket(zmq.REQ)
    socket.connect("ipc:///tmp/mksim")

    #  Do 10 requests, waiting each time for a response
    for request in range(10):
        print(f"Sending request {request} ...")
        socket.send_string("Hello")

        #  Get the reply.
        message = socket.recv()
        print(f"Received reply {request} [ {message} ]")

def test_zmq():
    server_process = Process(target=server)
    print("Starting server...")
    server_process.start()
    client_process = Process(target=client)
    client_process.start()
    client_process.join()
    print("Client finished.")
    server_process.kill()


def main():
    start_time = time.time()
    test_read(pod5_file)
    warn("This is a dummy warning..")
    end_time = time.time()
    print(f"Time elapsed: {end_time - start_time}")

if __name__ == '__main__':
    main()