import asyncio
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.config import settings
from app.handlers import register_exception_handlers
from app.kafka.infrastructure.kafka_consumer import KafkaConsumer
from app.kafka.infrastructure.kafka_producer import KafkaProducer
from app.logger import logger
from app.metics.metric_workers import update_orders_gauge
from app.outbox.application.usecases.kafka_worker import KafkaOutboxWorker
from app.services.container import Container
from app.services.orders.presentation.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Lifespan start")
    kafka_producer = KafkaProducer()
    await kafka_producer.start()
    logger.info("Kafka producer started (confirmed)")
    outbox_worker = KafkaOutboxWorker(kafka_producer=kafka_producer)
    asyncio.create_task(outbox_worker.start())

    handle_shipping_event_use_case = container.handle_shipping_event_use_case()

    async def handle_shipping_event(event: dict):
        await handle_shipping_event_use_case.execute(event)

    shipment_consumer = KafkaConsumer(
        topic=settings.KAFKA_SHIPMENT_TOPIC,
        group_id="order-service",
        handler=handle_shipping_event,
    )

    await shipment_consumer.start()
    asyncio.create_task(shipment_consumer.run())
    logger.info("Outbox worker task created")

    asyncio.create_task(update_orders_gauge())
    logger.info("Metric worker current by status was started")

    yield
    await container.catalog_client().close()


container = Container()

container.wire(
    modules=[
        "app.services.orders.presentation.routers",
    ]
)
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=settings.APP_ENV,
        release="1.0.0",
    )

app = FastAPI(lifespan=lifespan)

app.add_middleware(SentryAsgiMiddleware)


instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    env_var_name="ENABLE_METRICS",
)

instrumentator.instrument(app)

register_exception_handlers(app)

app.include_router(router, tags=["orders"])


@app.get("/metrics", include_in_schema=False)
async def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/error")
async def trigger_error():
    1 / 0
