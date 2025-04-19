FROM python:3.12-alpine
RUN apk add --no-cache git
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]