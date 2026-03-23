import json
import time

from aiokafka import AIOKafkaProducer
from app.config import settings
from app.logger import logger
from app.metics.metrics import kafka_messages_produced_total, kafka_produce_duration_seconds


class KafkaProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode(),
        )
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send(self, topic: str, value: dict):
        start = time.time()
        try:
            await self.producer.send(topic, value)
            kafka_messages_produced_total.labels(topic=topic).inc()
        finally:
            duration = time.time() - start
            kafka_produce_duration_seconds.labels(topic=topic).observe(duration)
