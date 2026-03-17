from uuid import UUID

from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from app.services.orders.application.use_cases.get_order import GetOrderUseCase
from app.services.orders.application.use_cases.payment_callback import (
    PaymentCallbackUseCase,
)
from app.services.container import Container
from app.services.orders.application.use_cases.create_order import CreateOrderUseCase
from app.services.orders.presentation.schemas import (
    CreateOrderSchem,
    ResponseOrderSchem,
    PaymentCallbackSchem,
)

router = APIRouter()


@router.post("/api/orders", response_model=ResponseOrderSchem, status_code=201)
@inject
async def create_order(
    data_order: CreateOrderSchem,
    use_case: CreateOrderUseCase = Depends(Provide[Container.create_order_use_case]),
):
    order = await use_case(data_order)
    return ResponseOrderSchem.from_domain(order)


@router.get("/api/orders/{order_id}", response_model=ResponseOrderSchem)
@inject
async def get_order(
    order_id: UUID,
    use_case: GetOrderUseCase = Depends(Provide[Container.get_order_use_case]),
):
    order = await use_case(order_id)
    return ResponseOrderSchem.from_domain(order)


@router.post("/api/orders/payment-callback")
@inject
async def payment_callback(
    callback: PaymentCallbackSchem,
    use_case: PaymentCallbackUseCase = Depends(
        Provide[Container.payment_callback_use_case]
    ),
):
    return await use_case(callback)
