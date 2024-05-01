FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./
RUN apk update && apk upgrade --no-cache && pip install --no-cache-dir -r requirements.txt
COPY app.py ./

CMD ["python", "./app.py"]