def get_logger(tag):
    pattern = '{}: {{}}'.format(tag)

    def logger_func(message):
        print(pattern.format(message))

    return logger_func
