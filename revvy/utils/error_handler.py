import sys
import traceback

from revvy.utils.logger import get_logger


def register_uncaught_exception_handler(logfile):
    log = get_logger('Exception logger')

    def log_uncaught_exception(exctype, value, tb):
        trace = "\t".join(traceback.format_tb(tb))
        log_message = f'Uncaught exception: {exctype}\nValue: {value}\nTraceback: \n\t{trace}\n\n'
        log(log_message)

        with open(logfile, 'a') as logf:
            logf.write(log_message)

    sys.excepthook = log_uncaught_exception
