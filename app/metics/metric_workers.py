import asyncio

from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.metics.metrics import orders_current_by_status
from app.services.core.models import Order


async def update_orders_gauge():
    while True:
        async with AsyncSessionLocal() as session:
            for status in ["NEW", "PAID", "SHIPPED", "CANCELLED"]:
                count = await session.scalar(
                    select(func.count()).where(Order.status == status)
                )
                orders_current_by_status.labels(status=status).set(count or 0)
        await asyncio.sleep(60)