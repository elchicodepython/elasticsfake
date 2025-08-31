from abc import ABC, abstractmethod
from typing import List


class BulkHandler(ABC):
    @abstractmethod
    def handle_bulk(self, bulk_data: List[dict]) -> None:
        """Process Elasticsearch bulk data"""
        pass
