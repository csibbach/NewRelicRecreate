FROM python:3.6
RUN mkdir -p /app

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

ADD . .
ENV NEW_RELIC_ENVIRONMENT=recreate
ENV NEW_RELIC_CONFIG_FILE=newrelic.ini
CMD ["python3", "-u","main.py"]
