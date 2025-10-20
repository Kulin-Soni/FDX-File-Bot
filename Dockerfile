FROM python:3.13-slim

WORKDIR /bot

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY /src .
CMD ["python", "main.py"]