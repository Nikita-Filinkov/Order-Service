import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.handlers import register_exception_handlers
from app.kafka.infrastructure.kafka_consumer import KafkaConsumer
from app.kafka.infrastructure.kafka_producer import KafkaProducer
from app.outbox.application.usecases.kafka_worker import KafkaOutboxWorker
from app.services.container import Container
from app.services.orders.presentation.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    kafka_producer = KafkaProducer()
    await kafka_producer.start()

    outbox_worker = KafkaOutboxWorker(kafka_producer=kafka_producer)
    asyncio.create_task(outbox_worker.start())

    handle_shipping_event_use_case = container.handle_shipping_event_use_case()

    async def handle_shipping_event(event: dict):
        await handle_shipping_event_use_case.execute(event)

    shipment_consumer = KafkaConsumer(
        topic=settings.KAFKA_SHIPMENT_TOPIC,
        group_id="order-service",
        handler=handle_shipping_event
    )

    await shipment_consumer.start()
    asyncio.create_task(shipment_consumer.run())

    yield
    await container.catalog_client().close()


container = Container()

container.wire(
    modules=[
        "app.services.orders.presentation.routers",
    ]
)

app = FastAPI()

register_exception_handlers(app)

app.include_router(router, tags=["orders"])
