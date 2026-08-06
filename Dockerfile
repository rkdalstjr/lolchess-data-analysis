# 공식 Playwright 이미지 (브라우저 내장)
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY crawler.py .
COPY preprocess.py .

CMD ["sh", "-c", "python /app/crawler.py && python /app/preprocess.py /data/input.json /data/output.csv"]