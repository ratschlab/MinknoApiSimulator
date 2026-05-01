import sys
import traceback
from time import localtime, strftime

class Log:
    @staticmethod
    def info(*args, **kwargs):
        msg = ("[{}][INFO]".format(strftime("%H:%M:%S", localtime())),) + args + ("",)
        print(*msg, file=sys.stderr, **kwargs)

    @staticmethod
    def status(*args, **kwargs):
        msg = ("\r[{}][STATUS]".format(strftime("%H:%M:%S", localtime())),) + args + ("",)
        print(*msg, file=sys.stderr, end='', **kwargs)

    @staticmethod
    def warn(*args, **kwargs):
        msg = ("[{}][WARN]".format(strftime("%H:%M:%S", localtime())),) + args + ("",)
        print(*msg, file=sys.stderr, **kwargs)
        traceback.print_stack(file=sys.stderr)

    @staticmethod
    def error(*args, **kwargs):
        msg = ("[{}][ERROR]".format(strftime("%H:%M:%S", localtime())),) + args + ("",)
        print(*msg, file=sys.stderr, **kwargs)
        raise RuntimeError()