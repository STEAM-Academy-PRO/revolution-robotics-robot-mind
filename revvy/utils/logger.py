from threading import Lock

_log_lock = Lock()


def get_logger(tag):
    prefix = tag + ': '

    def logger_func(message):
        with _log_lock:
            print(prefix + message)

    return lambda _: None # logger_func
