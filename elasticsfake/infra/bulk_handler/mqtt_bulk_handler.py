import logging
from typing import List
import paho.mqtt.client as mqtt
from domain.bulk_handler import BulkHandler
from domain.bulk_event import BulkEvent
from domain.event_transformer import EventTransformer


logger = logging.getLogger("elasticsfake")


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
    ):
        self.__event_transformer = event_transformer
        self.__topic = topic
        self.__qos = qos

        self.__client = mqtt.Client()
        if username and password:
            self.__client.username_pw_set(username, password)
        self.__client.connect(broker, port)

    def handle_bulk(self, events: List[BulkEvent]):

        for event in events:
            prepared_line = self.__event_transformer.transform_event(event)
            self.__add_to_topic(prepared_line)

        logger.debug("%s lines added to %s", len(events), self.__topic)

    def __add_to_topic(self, line: str):
        """Publishes an event to our configured MQTT topic."""
        self.__client.publish(self.__topic, line, qos=self.__qos)
        logger.debug("Published line to topic %s", self.__topic)
