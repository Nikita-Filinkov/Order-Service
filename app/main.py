from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.orders.infrastructure.container import Container
from app.orders.presentation.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await container.catalog_client().close()

container = Container()

container.wire(
    modules=[
        "app.orders.presentation.routers",
    ]
)

app = FastAPI()

app.include_router(router, tags=["orders"])

