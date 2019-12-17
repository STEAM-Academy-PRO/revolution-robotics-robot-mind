import sys
import traceback


def register_uncaught_exception_handler(logfile):
    def log_uncaught_exception(exctype, value, tb):
        log_message = 'Uncaught exception: {}\n' \
                      'Value: {}\n' \
                      'Traceback: \n\t{}\n' \
                      '\n'.format(exctype, value, "\t".join(traceback.format_tb(tb)))
        print(log_message)

        with open(logfile, 'a') as logf:
            logf.write(log_message)

    sys.excepthook = log_uncaught_exception
