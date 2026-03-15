from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.handlers import register_exception_handlers
from app.services.orders.infrastructure.container import Container
from app.services.orders.presentation.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
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
