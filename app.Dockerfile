FROM python:3.8

RUN apt-get update \
  && apt-get install -y unixodbc-dev libmariadb-dev-compat libz-dev default-mysql-client \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /coursys
COPY requirements.txt /coursys/requirements.txt

WORKDIR /coursys
RUN pip install -r requirements.txt

RUN useradd --home-dir /coursys --uid 1000 coursys
RUN chown coursys /coursys

COPY moss.zip /
RUN mkdir /moss && cd /moss && unzip /moss.zip

COPY . /coursys/
COPY docker/localsettings-proddev.py courses/localsettings.py
COPY docker/secrets-proddev.py courses/secrets.py

USER coursys

ENV PYTHONUNBUFFERED 1
CMD ./manage.py migrate && ./manage.py runserver 0:8000
