# coding: utf-8

from __future__ import print_function, absolute_import

import sys
import os.path
import argparse
import re
import bottle
try:
    import ujson as json
except ImportError:
    import json

from json import JSONDecoder

from datetime import datetime

from tinydb import TinyDB, Query
from tinydb_serialization import Serializer, SerializationMiddleware

from drop_parser import DropParserManager


class DatetimeSerializer(Serializer):
    OBJ_CLASS = datetime

    def encode(self, obj):
        return obj.strftime("%Y-%m-%dT%H:%M:%S")

    def decode(self, s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

def json_datetime_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("not serializable")

def _storage():
    _serializer = SerializationMiddleware()
    _serializer.register_serializer(DatetimeSerializer(), "DatetimeSerializer")
    return _serializer


def drop_collection():
    db = TinyDB("braindrops.json", storage=_storage())
    table = db.table("drops")
    return table


COLOR_TAG = "cyan"
COLOR_ATTR = "yellow"
COLOR_DATETIME = "blue"


try:
    from termcolor import colored
except ImportError:
    print ("INFO: improve display by installing termcolor with 'pip install termcolor'");
    def colored(message, *args, **kwargs):
        return message


def parser_drop(message):
    p = DropParserManager([
        'drop_parser.TagParser',
        'drop_parser.BirthdayAttrParser',
    ])
    return p.parse(message)


def _prettify_tags(message):

    def fnc(match):
        return colored(match.groups()[0], COLOR_TAG)

    return re.sub("(#\w+)", fnc, message)


def _prettify_attrs(message):

    def fnc(match):
        return colored("%s:%s" % match.groups(0), COLOR_ATTR)

    return re.sub("(@\w+):([\w+\_\-\.]+)", fnc, message)


def _prettify(drop, full=False):
    resp = []
    resp.append(" ".join([colored("{%s}" %drop.eid, "red"), colored(drop['datetime'], COLOR_DATETIME)]))
    resp.append(_prettify_attrs(_prettify_tags(drop['message'])))
    if full:
        resp.append("tags: {}".format(colored(", ".join(drop['tags']), "green")))
        resp.append("attrs: {}".format(drop['attrs']))
    return "\n".join(resp)


def _add(message):
    drop = parser_drop(message)
    drops = drop_collection()
    eid = drops.insert(drop)
    return _get(eid)


def cmd_add(args):
    drop = _add(" ".join(args.message))
    print(_prettify(drop, full=True))


def _list(tags=None, limit=10):
    drops = drop_collection()

    if not tags:
        tags = list()

    if tags:
        Drop = Query()
        from operator import __or__
        search_query = reduce(__or__, [
            Drop.tags.test(lambda l: tag in l) for tag in tags
        ])
        query = drops.search(search_query)
    else:
        query = drops.all()
    query = sorted(query, key=lambda o: o['datetime'], reverse=True)
    query = query[:limit]
    for drop in query:
        yield drop

def cmd_list(args):
    for drop in _list(tags=args.tags, limit=args.limit):
        print(_prettify(drop, full=args.full))
        print()

def _tags():
    from collections import defaultdict
    tags = defaultdict(int)
    drops = drop_collection()
    for drop in drops.all():
        for tag in drop['tags']:
            tags[tag] += 1
    for tag, count in sorted(tags.items(), key=lambda o: o[1], reverse=True):
        yield tag, count

def cmd_tags(args):
    for tag, count in _tags():
        print("%s: %s" % (tag, count))

def _get(eid):
    drops = drop_collection()
    return drops.get(eid=eid)


def cmd_get(args):
    print(_prettify(_get(args.id)))


def _remove(eid):
    drops = drop_collection()
    drops.remove(eids=[eid])


def cmd_remove(args):
    _remove(args.id)
    print("ok")


def _rest(args):

    from bottle import response, request

    def to_json(value):
        return json.dumps(dict(value, id=value.eid), default=json_datetime_serial)

    @bottle.route("/drops", method="GET")
    def list():
        response.content_type = "application/json"
        return map(to_json, _list())

    @bottle.route("/drops", method="PUT")
    def create():
        payload = request.json
        return to_json(_add(payload['message']))

    @bottle.route("/drops/<eid:int>", method="GET")
    def get(eid):
        eid = int(eid)
        response.content_type = "application/json"
        return to_json(_get(eid))

    @bottle.route("/drops/<eid:int>", method="POST")
    def update(eid):
        pass

    @bottle.route("/drops/<eid:int>", method="DELETE")
    def delete(eid):
        eid = int(eid)
        _remove(eid)
        response.content_type = "application/json"
        return json.dumps(["ok"])

    bottle.run(debug=True, reloader=True)


parser = argparse.ArgumentParser(prog=__file__)
sub_parsers = parser.add_subparsers()

add_parser = sub_parsers.add_parser("add")
add_parser.add_argument("message", metavar="M", type=str, nargs="+")
add_parser.set_defaults(func=cmd_add)

list_parser = sub_parsers.add_parser("list")
list_parser.add_argument("--full", "-f", dest="full", action="store_true", default=False)
list_parser.set_defaults(func=cmd_list)
list_parser.add_argument("--tag", "-t", dest="tags", action="append", default=[])
list_parser.add_argument("--limit", "-l", dest="limit", type=int, default=5)

rm_parser = sub_parsers.add_parser("rm")
rm_parser.add_argument("id", metavar="ID", type=int)
rm_parser.set_defaults(func=cmd_remove)

get_parser = sub_parsers.add_parser("get")
get_parser.set_defaults(func=cmd_get)
get_parser.add_argument("id", metavar="ID", type=int)

rest_parser = sub_parsers.add_parser("rest")
rest_parser.set_defaults(func=_rest)

tags_parser = sub_parsers.add_parser("tags")
tags_parser.set_defaults(func=cmd_tags)


if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)
