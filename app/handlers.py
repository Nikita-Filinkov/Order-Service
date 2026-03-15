from fastapi import FastAPI
from app.orders.catalog_service.exceptions import (
    NotItemException,
    QuantityException,
    ProviderTemporaryError,
)
from app.orders.exceptions import (
    NotItemCatalogException,
    QuantityCatalogException,
    OrderNotRequestException,
)


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(NotItemException)
    async def not_item_handler(request, exc):
        raise NotItemCatalogException

    @app.exception_handler(QuantityException)
    async def quantity_handler(request, exc):
        raise QuantityCatalogException

    @app.exception_handler(ProviderTemporaryError)
    async def provider_temporary_handler(request, exc):
        raise OrderNotRequestException
