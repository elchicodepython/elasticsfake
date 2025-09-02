import json


class BulkEvent:
    def __init__(self, metadata_line: str, doc_line: str):
        self.metadata_line = metadata_line
        self.meta = json.loads(metadata_line)
        self.doc_line = doc_line
        self.doc = json.loads(doc_line)

    @property
    def index(self) -> str:
        if "index" in self.meta:
            return self.meta["index"]["_index"]
        elif "create" in self.meta:
            return self.meta["create"]["_index"]
        else:
            raise ValueError("No _index found in meta")
