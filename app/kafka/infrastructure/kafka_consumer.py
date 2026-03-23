import json
import time

from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.logger import logger
from app.metics.metrics import kafka_consume_processing_duration_seconds, kafka_messages_consumed_total, \
    kafka_consume_errors_total


class KafkaConsumer:
    def __init__(self, topic: str, group_id: str, handler):
        self.topic = topic
        self.group_id = group_id
        self.handler = handler
        self.consumer = None

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode()),
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        )
        await self.consumer.start()
        logger.info(f"Kafka consumer for {self.topic} started")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()

    async def run(self):
        async for msg in self.consumer:
            topic = msg.topic
            event_type = msg.value.get("event_type", "unknown")
            start = time.time()
            try:
                await self.handler(msg.value)
                kafka_messages_consumed_total.labels(topic=topic).inc()
            except Exception as e:
                error_type = type(e).__name__
                kafka_consume_errors_total.labels(topic=topic, error_type=error_type).inc()
                logger.error(f"Error processing message: {e}")
                continue
            finally:
                duration = time.time() - start
                kafka_consume_processing_duration_seconds.labels(topic=topic, event_type=event_type).observe(duration)
            await self.consumer.commit()
