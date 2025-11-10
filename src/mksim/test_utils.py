from .logs import *

RED   = "\x1B[31m"
GRN   = "\x1B[32m"
YEL   = "\x1B[33m"
BLU   = "\x1B[34m"
MAG   = "\x1B[35m"
CYN   = "\x1B[36m"
RESET = "\x1B[0m"

def _print_vector(name, vector):
    n = len(vector)
    print("{}:".format(name))
    if n > 20: print(vector[:10], '...', vector[-10:])
    else: print(vector)

def print_vectors(**kwargs):
    for k, v in kwargs.items(): _print_vector(k, v)


def blurt(*args, color=GRN):
    msg = (color,) + args + (RESET,)
    print(*msg, end=' ')