FROM python:3.8


RUN apt-get update \
  && apt-get install -y unixodbc-dev libmariadb-dev-compat libz-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /coursys
COPY requirements.txt /coursys/requirements.txt

WORKDIR /coursys
RUN pip install -r requirements.txt


# RUN apt-get update \
#   && apt-get install -y asdfasf \
#   && apt-get clean \
#   && rm -rf /var/lib/apt/lists/*

COPY . /coursys/
