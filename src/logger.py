import logging
import os


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ApplicationLogger(metaclass=Singleton):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.basedir = os.path.abspath(os.path.abspath(os.path.dirname(__file__)))

        log_file = f'{self.basedir}/application.log'
        file_log = logging.FileHandler(log_file)
        console_out = logging.StreamHandler()

        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(log_format)

        file_log.setFormatter(formatter)
        console_out.setFormatter(formatter)
        self.logger.addHandler(file_log)
        self.logger.addHandler(console_out)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


logger = ApplicationLogger()