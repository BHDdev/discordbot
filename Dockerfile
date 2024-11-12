FROM python:3.13-alpine
RUN apk add --no-cache git
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]