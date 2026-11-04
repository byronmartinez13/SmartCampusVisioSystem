FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.lock.txt ./requirements.lock.txt
RUN pip install --no-cache-dir -r requirements.lock.txt
RUN useradd --create-home --uid 10001 campus
COPY backend/ ./
RUN mkdir -p /app/private-media /app/staticfiles && chown -R campus:campus /app
USER campus
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "180", "--access-logfile", "-"]
