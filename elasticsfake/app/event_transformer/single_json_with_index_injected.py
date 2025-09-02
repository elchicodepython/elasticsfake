from domain.event_transformer import EventTransformer
from domain.bulk_event import BulkEvent
import json


class SingleJsonWithIndexInjected(EventTransformer):
    def transform_event(self, bulk_event: BulkEvent) -> str:
        document = bulk_event.doc
        document["_index"] = bulk_event.index
        return json.dumps(document)
