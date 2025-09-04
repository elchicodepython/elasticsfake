import signal
from domain.bulk_handler import BulkHandler
from infra.bulk_handler import FileBulkHandler, MqttBulkHandler
from app.event_transformer import SingleJsonWithIndexInjected


def configure_file_bulk_handler(conf: dict) -> BulkHandler:
    file_path = conf["infra.bulk_handler.file.path"]
    max_bytes = conf.get(
        "infra.bulk_handler.file.max_bytes_before_rotation", 10 * 1024 * 1024
    )  # 10 MB
    backup_count = conf.get("infra.bulk_handler.file.rotated_files", 5)

    event_transformer = SingleJsonWithIndexInjected()

    return FileBulkHandler(file_path, event_transformer, max_bytes, backup_count)


def configure_mqtt_bulk_handler(conf: dict) -> BulkHandler:
    broker = conf["infra.bulk_handler.mqtt.broker"]
    port = conf.get("infra.bulk_handler.mqtt.port", 1883)
    topic = conf["infra.bulk_handler.mqtt.topic"]
    qos = conf.get("infra.bulk_handler.mqtt.qos", 1)
    username = conf.get("infra.bulk_handler.mqtt.username", None)
    password = conf.get("infra.bulk_handler.mqtt.password", None)

    event_transformer = SingleJsonWithIndexInjected()

    return MqttBulkHandler(
        event_transformer, broker, port, topic, qos, username, password
    )


def configure_bulk_handler(conf: dict) -> BulkHandler:
    handler_type = conf.get("infra.bulk_handler.type", "file").lower()

    if handler_type == "file":
        handler = configure_file_bulk_handler(conf)
    elif handler_type == "mqtt":
        handler = configure_mqtt_bulk_handler(conf)
    else:
        raise ValueError(f"Unsupported bulk handler type: {handler_type}")

    signal.signal(signal.SIGINT, lambda *_: handler.hook_terminate())
    signal.signal(signal.SIGTERM, lambda *_: handler.hook_terminate())

    return handler