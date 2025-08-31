from domain.bulk_handler import BulkHandler
from infra.bulk_handler import FileBulkHandler


def configure_bulk_handler(conf: dict) -> BulkHandler:
    file_path = conf["infra.bulk_handler.file.path"]
    max_bytes = conf.get(
        "infra.bulk_handler.file.max_bytes_before_rotation", 10 * 1024 * 1024
    )  # 10 MB
    backup_count = conf.get("infra.bulk_handler.file.rotated_files", 5)

    return FileBulkHandler(file_path, max_bytes, backup_count)
