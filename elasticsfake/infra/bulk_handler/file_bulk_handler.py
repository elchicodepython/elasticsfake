import logging
import json
from typing import Dict, List
from domain.bulk_handler import BulkHandler


logger = logging.getLogger("elasticsfake")
formatter = logging.Formatter("%(message)s")


class FileBulkHandler(BulkHandler):
    def __init__(self, file_path: str, max_bytes: int, backup_count: int):
        self.__file_path = file_path
        self.__file_logger = logging.getLogger("infra.bulk_handler.file_bulk_handler")

        file_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self.__file_logger.addHandler(file_handler)

    def handle_bulk(self, events: List[Dict[str, str]]):

        for event in events:
            prepared_line = self.__create_singleline_from_event(event)
            self.__append_to_file(prepared_line)

        logger.debug("%s lines added to %s", len(events), self.__file_path)

    def __create_singleline_from_event(self, event: Dict[str, str]) -> str:
        meta = json.loads(event["meta"])
        document = json.loads(event["doc"])

        # Injects _index metadata into the document line
        if "_index" in meta:
            document["_index"] = meta["index"]["_index"]
        elif "create" in meta:
            document["_index"] = meta["create"]["_index"]
        else:
            logger.error("No _index found in meta: %s", meta)

        return json.dumps(document)

    def __append_to_file(self, line: str):
        """Writes an event to our configured file rotating the file when needed."""

        # Instead of making a manual rotation or relying on a external library
        # for it, i'm using here a nice "trick" with a custom logger.
        # As the python logging library already have this functionality built-in
        # im relying on it to write lines to a file and rotating the file when
        # needed ;)

        self.__file_logger.critical(line)
