FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# ставим uv
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

# сначала только метаданные зависимостей (для кеша)
COPY pyproject.toml uv.lock ./

# ставим зависимости строго по lock
RUN uv sync --frozen --no-dev

# затем код
COPY . .

# RUN mkdir -p /app/images \
#              /app/images/works \
#              /app/images/avatars \
#              /app/images/collages \
#              /app/images/new_avatars \
#              /app/images/new_collages \
#              /app/images/new_works

CMD ["uv", "run", "python", "-m", "src.main"]


