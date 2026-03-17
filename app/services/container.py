from dependency_injector import containers, providers
from app.database import AsyncSessionLocal
from app.services.orders.application.use_cases.get_order import GetOrderUseCase
from app.services.catalog_service.infrastructure.catalog import CatalogClient
from app.services.orders.application.use_cases.handle_shipping_event import HandleShippingEventUseCase
from app.services.orders.application.use_cases.payment_callback import (
    PaymentCallbackUseCase,
)
from app.services.orders.infrastructure.unit_of_work import UnitOfWork
from app.services.orders.application.use_cases.create_order import CreateOrderUseCase
from app.services.payment_service.infrastructure.client import PaymentClient


class Container(containers.DeclarativeContainer):
    """Главный контейнер приложения"""

    session_factory = providers.Object(AsyncSessionLocal)

    unit_of_work = providers.Factory(
        UnitOfWork,
        session_factory=session_factory,
    )

    catalog_client = providers.Singleton(CatalogClient)
    payment_client = providers.Singleton(PaymentClient)

    create_order_use_case = providers.Factory(
        CreateOrderUseCase,
        unit_of_work=unit_of_work,
        catalog_client=catalog_client,
        payment_client=payment_client,
    )

    get_order_use_case = providers.Factory(
        GetOrderUseCase,
        unit_of_work=unit_of_work,
    )

    payment_callback_use_case = providers.Factory(
        PaymentCallbackUseCase,
        unit_of_work=unit_of_work,
    )

    handle_shipping_event_use_case = providers.Factory(
        HandleShippingEventUseCase,
        unit_of_work=unit_of_work,
    )
