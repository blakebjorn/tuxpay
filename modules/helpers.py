import asyncio
import base64
import datetime
import functools
import gzip
import json
import os
import random
import secrets
import string
from collections.abc import Mapping
from decimal import Decimal

from sqlalchemy.engine import RowProxy
from starlette.responses import Response


def sanitize_filename(e, allow_periods=True):
    for char in ('\\/:*?"<>|' + ("." if not allow_periods else "")):
        if char in e:
            e = e.replace(char, "_")
    return e


def left_pad(inp: str, length: int, padding: str = "0") -> str:
    while len(inp) < length:
        inp = padding + inp
    return inp


def to_b64(inp: bytes) -> str:
    return base64.b64encode(inp).decode('utf8')


def from_b64(inp: str) -> bytes:
    return base64.b64decode(inp.encode('utf8'))


def random_alphanumeric_string(length, subset="alpha", secure=False):
    if subset == "alpha":
        dat = string.ascii_letters + string.digits
    elif subset == "all":
        dat = string.digits + string.ascii_letters + string.punctuation
    elif subset == "hex":
        dat = string.digits + 'abcdef'
    else:
        raise NotImplementedError

    if secure:
        return ''.join((secrets.choice(dat) for _ in range(length)))
    return ''.join(random.choices(dat, k=length))


def age_hours(timestamp):
    return (datetime.datetime.now().timestamp() - timestamp) / 3600


async def run_async(fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))


def _json_encoder(i):
    if isinstance(i, Mapping) or isinstance(i, RowProxy):
        return dict(i)
    if isinstance(i, datetime.datetime):
        return i.replace(tzinfo=datetime.timezone.utc).timestamp()
    elif isinstance(i, datetime.date):
        return datetime.datetime(i.year, i.month, i.day).replace(tzinfo=datetime.timezone.utc).timestamp()
    if isinstance(i, Decimal):
        return float(i)
    if isinstance(i, set):
        return list(i)
    if isinstance(i, bytes):
        return i.decode("utf-8")
    return TypeError(f"Unserializable object of type {type(i)} - {repr(i)}")


def int_or_none(val):
    if val is None or isinstance(val, int):
        return val
    try:
        return int(round(float(val)))
    except ValueError:
        return None


def timestamp():
    """
    JS style timestamp (unix timestamp * 1000)
    :return: integer
    """
    return int(datetime.datetime.now().timestamp() * 1000)


def to_json(obj, **kwargs) -> str:
    return json.dumps(obj, default=_json_encoder, **kwargs)


def read_json(path, default):
    try:
        with open(path, 'r') as f:
            r = json.loads(f.read())
    except:
        r = default
    return r


def read_json_gz(filename, default):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with gzip.open(path, 'rb') as f:
            data = f.read()
            r = json.loads(data.decode('utf-8'))
    except:
        r = default
    return r


def inv_dict(d):
    return {v: k for k, v in d.items()}


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return to_json(content,
                       ensure_ascii=False,
                       allow_nan=False,
                       indent=None,
                       separators=(",", ":")).encode("utf-8")


EPOCH = datetime.datetime.utcfromtimestamp(0)
NOT_FOUND = JSONResponse({"error": "not found"}, status_code=404)
NOT_AUTHENTICATED = JSONResponse({"error": "not authenticated"}, status_code=401)
