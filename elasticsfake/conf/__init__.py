from .conf_confdict import configure_confdict
from .conf_bulk_handler import configure_bulk_handler
from .conf_logger import configure_logger


class Container:
    def __init__(self):
        self.confdict = configure_confdict()
        configure_logger(self.confdict)
        self.bulk_handler = configure_bulk_handler(self.confdict)


container = Container()
