def Logger(tag):
    pattern = '{}: {{}}'.format(tag)

    def logger_func(message):
        print(pattern.format(message))

    return logger_func
