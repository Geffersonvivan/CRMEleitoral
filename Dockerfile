FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "echo '==> Migrate...' && python manage.py migrate --noinput && echo '==> Collectstatic...' && python manage.py collectstatic --noinput && echo '==> Starting gunicorn on port $PORT...' && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --log-level info"
