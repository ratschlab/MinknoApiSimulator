import sys
import traceback
from time import localtime, strftime

def info(*args, **kwargs):
    msg = ("[{}]\x1B[32mINFO:".format(strftime("%H:%M:%S", localtime())),) + args + ("\x1B[0m",)
    print(*msg, file=sys.stderr, **kwargs)


def status(*args, **kwargs):
    msg = ("\r[{}]\x1B[35mSTATUS:".format(strftime("%H:%M:%S", localtime())),) + args + ("\x1B[0m",)
    print(*msg, file=sys.stderr, end='', **kwargs)


def warn(*args, **kwargs):
    msg = ("[{}]\x1B[33mWARN:".format(strftime("%H:%M:%S", localtime())),) + args + ("\x1B[0m",)
    print(*msg, file=sys.stderr, **kwargs)
    traceback.print_stack(file=sys.stderr)


def error(*args, **kwargs):
    msg = ("[{}]\x1B[31mERROR:".format(strftime("%H:%M:%S", localtime())),) + args + ("\x1B[0m",)
    print(*msg, file=sys.stderr, **kwargs)
    raise RuntimeError()