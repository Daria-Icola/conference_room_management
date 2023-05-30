FROM python:3.8.10

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/code

WORKDIR /code

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD python run_polling.py

