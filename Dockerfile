FROM python:3.13-slim

WORKDIR /app

COPY src/ /app/src/
COPY bench.py /app/

ENV PORT=8080 \
    HOST=0.0.0.0

EXPOSE 8080

CMD ["python3", "-m", "src.gateway"]
