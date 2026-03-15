from dependency_injector import containers, providers
from app.database import AsyncSessionLocal
from app.orders.application.use_cases.get_order import GetOrderUseCase
from app.orders.catalog_service.infrastructure.catalog import CatalogClient
from app.orders.infrastructure.unit_of_work import UnitOfWork
from app.orders.application.use_cases.create_order import CreateOrderUseCase


class Container(containers.DeclarativeContainer):
    """Главный контейнер приложения"""

    session_factory = providers.Object(AsyncSessionLocal)

    unit_of_work = providers.Factory(
        UnitOfWork,
        session_factory=session_factory,
    )

    catalog_client = providers.Singleton(CatalogClient)

    create_order_use_case = providers.Factory(
        CreateOrderUseCase, unit_of_work=unit_of_work, catalog_client=catalog_client
    )

    get_order_use_case = providers.Factory(
        GetOrderUseCase,
        unit_of_work=unit_of_work,
    )
