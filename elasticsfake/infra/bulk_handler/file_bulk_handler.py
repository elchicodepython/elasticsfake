import logging
from typing import List
from domain.bulk_handler import BulkHandler
from domain.bulk_event import BulkEvent
from domain.event_transformer import EventTransformer

logger = logging.getLogger("elasticsfake")
formatter = logging.Formatter("%(message)s")


class FileBulkHandler(BulkHandler):
    def __init__(
        self,
        file_path: str,
        event_transformer: EventTransformer,
        max_bytes: int,
        backup_count: int,
    ):
        self.__file_path = file_path
        self.__file_logger = logging.getLogger("infra.bulk_handler.file_bulk_handler")
        self.__event_transformer = event_transformer

        file_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self.__file_logger.addHandler(file_handler)

    def handle_bulk(self, events: List[BulkEvent]):

        for event in events:
            prepared_line = self.__event_transformer.transform_event(event)
            self.__append_to_file(prepared_line)

        logger.debug("%s lines added to %s", len(events), self.__file_path)

    def __append_to_file(self, line: str):
        """Writes an event to our configured file rotating the file when needed."""

        # Instead of making a manual rotation or relying on a external library
        # for it, i'm using here a nice "trick" with a custom logger.
        # As the python logging library already have this functionality built-in
        # im relying on it to write lines to a file and rotating the file when
        # needed ;)

        self.__file_logger.critical(line)
