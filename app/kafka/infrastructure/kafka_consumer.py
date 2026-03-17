import json
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.logger import logger


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
            try:
                await self.handler(msg.value)
                await self.consumer.commit()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
