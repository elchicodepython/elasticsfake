from abc import ABC, abstractmethod
from typing import List
from .bulk_event import BulkEvent


class BulkHandler(ABC):
    @abstractmethod
    def handle_bulk(self, bulk_data: List[BulkEvent]) -> None:
        """Process Elasticsearch bulk data"""
        pass

    def hook_terminate(self):
        pass
