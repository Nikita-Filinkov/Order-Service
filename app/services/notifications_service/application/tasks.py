from app.logger import logger
from app.services.notifications_service.dto import SendNotificationRequestDTO
from app.services.notifications_service.exceptions import NotificationTemporaryError
from app.services.notifications_service.infrastructure.client import NotificationClient


async def send_status_notification(
    notification_client: NotificationClient,
    order_id: str,
    status: str,
    idempotency_key: str,
    reason: str = None,
):
    """Функция отправки уведомления"""

    messages = {
        "NEW": "Ваш заказ создан и ожидает оплаты",
        "PAID": "Ваш заказ успешно оплачен и готов к отправке",
        "SHIPPED": "Ваш заказ отправлен в доставку",
        "CANCELLED": f"Ваш заказ отменен. Причина: {reason or 'неизвестна'}",
    }
    message = messages.get(status)
    if not message:
        logger.error(f"Unknown status for notification: {status}")
        return

    dto = SendNotificationRequestDTO(
        message=message,
        reference_id=order_id,
        idempotency_key=idempotency_key,
    )
    try:
        await notification_client.send_notification(dto)
        logger.info(f"Notification sent for order {order_id} with status {status}")
    except NotificationTemporaryError as e:
        logger.error(f"Failed to send notification for order {order_id}: {e.message}")
    except Exception:
        logger.exception(f"Unexpected error sending notification for order {order_id}")
