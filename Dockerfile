# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 스크립트 복사
COPY preprocess.py .

# 기본 실행 명령어
ENTRYPOINT ["python", "/app/preprocess.py"]