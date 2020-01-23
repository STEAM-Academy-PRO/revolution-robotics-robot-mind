from threading import Lock

_log_lock = Lock()


def get_logger(tag):
    pattern = f'{tag}: {{}}'

    def logger_func(message):
        with _log_lock:
            print(pattern.format(message))

    return logger_func
