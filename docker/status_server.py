#!/usr/bin/env python

# docker compose -f compose-demo.yml run celery-batch curl host.docker.internal:8888/stats/json


import subprocess
from typing import Union

import flask


app = flask.Flask(__name__)
Response = Union[flask.Response, str]


@app.route('/')
def index() -> Response:
    return "hi"


def with_format(cmd: list[str], format: str) -> Response:
    match format:
        case 'table':
            media_type = 'text/plain'
        case 'json':
            media_type = 'application/jsonl'
        case _:
            return ''
        
    p = subprocess.Popen(cmd + ["--format", format], stdout=subprocess.PIPE)
    return flask.Response(response=p.stdout, status=200, mimetype=media_type)


@app.route('/stats', defaults={'format': 'table'})
@app.route('/stats/<format>')
def stats(format) -> Response:
    return with_format(["docker", "compose", "stats", "--no-stream"], format)


@app.route('/ps', defaults={'format': 'table'})
@app.route('/ps/<format>')
def ps(format) -> Response:
    return with_format(["docker", "compose", "ps"], format)
