FROM python:3.11-slim

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser

WORKDIR /service
RUN chown -R appuser:appuser /service

COPY pyproject.toml uv.lock ./

RUN pip install uv && \
    uv sync --frozen --no-dev

COPY . .

RUN chmod a+x /service/docker/*.sh

ENV PATH="/service/.venv/bin:$PATH"

USER appuser

CMD ["/service/docker/app.sh"]