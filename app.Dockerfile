FROM python:3.8

RUN apt-get update \
  && apt-get install -y unixodbc-dev libmariadb-dev-compat libz-dev default-mysql-client \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /coursys
COPY requirements.txt /coursys/requirements.txt

WORKDIR /coursys
RUN pip install -r requirements.txt

COPY . /coursys/

ENV PYTHONUNBUFFERED 1
CMD ./manage.py runserver 0:8000

COPY docker/localsettings-proddev.py courses/localsettings.py
COPY docker/secrets-proddev.py courses/secrets.py
