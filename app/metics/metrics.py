from prometheus_client import Counter, Gauge, Histogram

orders_created_total = Counter("orders_created_total", "Total number of orders created")
orders_paid_total = Counter("orders_paid_total", "Total number of orders paid")
orders_shipped_total = Counter("orders_shipped_total", "Total number of orders shipped")
orders_cancelled_total = Counter(
    "orders_cancelled_total", "Total number of orders cancelled"
)

orders_current_by_status = Gauge(
    "orders_current_by_status",
    "Current number of orders by status",
    labelnames=["status"],
)

catalog_requests_total = Counter(
    "catalog_requests_total",
    "Total requests to Catalog Service",
    labelnames=["endpoint", "status"],
)

catalog_request_duration = Histogram(
    "catalog_request_duration_seconds",
    "Duration of requests to Catalog Service",
    labelnames=["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

payment_requests_total = Counter(
    "payment_requests_total",
    "Total requests to Payment Service",
    labelnames=["endpoint", "status"],
)
payment_request_duration = Histogram(
    "payment_request_duration_seconds",
    "Duration of requests to Payment Service",
    labelnames=["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Notification Service
notification_requests_total = Counter(
    "notification_requests_total",
    "Total requests to Notification Service",
    labelnames=["endpoint", "status"],
)
notification_request_duration = Histogram(
    "notification_request_duration_seconds",
    "Duration of requests to Notification Service",
    labelnames=["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

kafka_messages_produced_total = Counter(
    "kafka_messages_produced_total",
    "Total number of messages produced to Kafka",
    labelnames=["topic"],
)
kafka_produce_duration_seconds = Histogram(
    "kafka_produce_duration_seconds",
    "Duration of producing a message to Kafka",
    labelnames=["topic"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

kafka_messages_consumed_total = Counter(
    "kafka_messages_consumed_total",
    "Total number of messages consumed from Kafka",
    labelnames=["topic"],
)
kafka_consume_processing_duration_seconds = Histogram(
    "kafka_consume_processing_duration_seconds",
    "Duration of processing a Kafka message",
    labelnames=["topic", "event_type"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
kafka_consume_errors_total = Counter(
    "kafka_consume_errors_total",
    "Total errors while processing Kafka messages",
    labelnames=["topic", "error_type"],
)
