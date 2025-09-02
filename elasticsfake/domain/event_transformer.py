from abc import ABC, abstractmethod
from .bulk_event import BulkEvent


class EventTransformer(ABC):
    @abstractmethod
    def transform_event(self, bulk_event: BulkEvent) -> str:
        """Transforms an event before storing or forwarding it"""
        pass
