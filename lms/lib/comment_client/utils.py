from contextlib import contextmanager
from dogapi import dog_stats_api
import json
import logging
import requests
import settings
from time import time
from uuid import uuid4

log = logging.getLogger(__name__)


def strip_none(dic):
    return dict([(k, v) for k, v in dic.iteritems() if v is not None])


def strip_blank(dic):
    def _is_blank(v):
        return isinstance(v, str) and len(v.strip()) == 0
    return dict([(k, v) for k, v in dic.iteritems() if not _is_blank(v)])


def extract(dic, keys):
    if isinstance(keys, str):
        return strip_none({keys: dic.get(keys)})
    else:
        return strip_none({k: dic.get(k) for k in keys})


def merge_dict(dic1, dic2):
    return dict(dic1.items() + dic2.items())


@contextmanager
def request_timer(request_id, method, url):
    start = time()
    yield
    end = time()
    duration = end - start
    dog_stats_api.histogram('comment_client.request.time', duration, end)
    log.info(
        "comment_client_request_log: request_id={request_id}, method={method}, "
        "url={url}, duration={duration}".format(
            request_id=request_id,
            method=method,
            url=url,
            duration=duration
        )
    )


def perform_request(method, url, data_or_params=None, *args, **kwargs):
    if data_or_params is None:
        data_or_params = {}
    headers = {'X-Edx-Api-Key': settings.API_KEY}
    request_id = uuid4()
    request_id_dict = {'request_id': request_id}

    if method in ['post', 'put', 'patch']:
        data = data_or_params
        params = request_id_dict
    else:
        data = None
        params = merge_dict(data_or_params, request_id_dict)
    with request_timer(request_id, method, url):
        response = requests.request(
            method,
            url,
            data=data,
            params=params,
            headers=headers,
            timeout=5
        )

    if 200 < response.status_code < 500:
        raise CommentClientRequestError(response.text, response.status_code)
    # Heroku returns a 503 when an application is in maintenance mode
    elif response.status_code == 503:
        raise CommentClientMaintenanceError(response.text)
    elif response.status_code == 500:
        raise CommentClient500Error(response.text)
    else:
        if kwargs.get("raw", False):
            return response.text
        else:
            return json.loads(response.text)


class CommentClientError(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return repr(self.message)


class CommentClientRequestError(CommentClientError):
    def __init__(self, msg, status_code=400):
        super(CommentClientRequestError, self).__init__(msg)
        self.status_code = status_code


class CommentClient500Error(CommentClientError):
    pass


class CommentClientMaintenanceError(CommentClientError):
    pass
