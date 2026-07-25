import logging, time
from typing import List
import paho.mqtt.client as mqtt
from domain.bulk_handler import BulkHandler
from domain.bulk_event import BulkEvent
from domain.event_transformer import EventTransformer


logger = logging.getLogger("elasticsfake")


def on_connect(_client, _userdata, _flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
    else:
        logger.error("Broker connection failed with code %s", rc)


def on_disconnect(_client, _userdata, rc):
    if rc == 0:
        logger.info("Disconnected from MQTT broker")
    else:
        logger.warning(
            "Lost connection to MQTT broker (code %s), reconnecting...", rc
        )


class MqttBulkHandler(BulkHandler):
    def __init__(
        self,
        event_transformer: EventTransformer,
        broker: str,
        port: int,
        topic: str,
        qos: int = 1,
        username: str = None,
        password: str = None,
        connect_timeout: float = 30,
    ):
        self.__event_transformer = event_transformer
        self.__topic = topic
        self.__qos = qos

        self.__client = mqtt.Client()
        self.__client.on_connect = on_connect
        self.__client.on_disconnect = on_disconnect
        self.__client.reconnect_delay_set(min_delay=1, max_delay=30)

        if username and password:
            self.__client.username_pw_set(username, password)

        self.__client.connect(broker, port)
        self.__client.loop_start()

        # Wait for the initial connection to be established, bounded so a
        # dead/unreachable broker fails fast instead of hanging forever.
        waited = 0.0
        while not self.__client.is_connected():
            if waited >= connect_timeout:
                self.__client.loop_stop()
                raise ConnectionError(
                    f"Could not connect to MQTT broker {broker}:{port} "
                    f"within {connect_timeout}s"
                )
            logger.debug("Waiting for MQTT connection...")
            time.sleep(0.1)
            waited += 0.1

    def handle_bulk(self, events: List[BulkEvent]):
        for event in events:
            prepared_line = self.__event_transformer.transform_event(event)
            self.__add_to_topic(prepared_line)

        logger.debug("%s lines added to %s", len(events), self.__topic)

    def __add_to_topic(self, line: str):
        """Publishes an event to our configured MQTT topic."""
        msg_info = self.__client.publish(self.__topic, line, qos=self.__qos)
        msg_info.wait_for_publish()
        logger.debug("Published line to topic %s", self.__topic)
    
    def hook_terminate(self):
        self.__client.loop_stop()
        self.__client.disconnect()
        logger.debug("Disconnected from MQTT broker")
