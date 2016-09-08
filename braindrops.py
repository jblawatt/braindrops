# coding: utf-8

from __future__ import print_function, absolute_import

import sys
import os.path
import argparse
import re
import bottle

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

def _storage():
    _serializer = SerializationMiddleware()
    _serializer.register_serializer(DatetimeSerializer(), "DatetimeSerializer")
    return _serializer


db = TinyDB("braindrops.json", storage=_storage())

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
    print(colored("{%s}" %drop.eid, "red"), colored(drop['datetime'], COLOR_DATETIME))
    print(_prettify_attrs(_prettify_tags(drop['message'])))
    if full:
        print("tags: {}".format(colored(", ".join(drop['tags']), "green")))
        print("attrs: {}".format(drop['attrs']))


def _add(args):
    drop = parser_drop(" ".join(args.message))
    drops = db.table("drops")
    drops.insert(drop)


def _list(args):
    drops = db.table("drops")

    if args.tags:
        Drop = Query()
        for tag in args.tags:
            query = drops.search(Drop.tags.test(lambda v: tag in v))
    else:
        query = drops.all()
    query = sorted(query, key=lambda o: o['datetime'], reverse=True)
    query = query[:args.limit]
    for drop in query:
        _prettify(drop, full=args.full)
        print()

def _get(args):
    drops = db.table("drops")
    drop = drops.get(eid=args.id)
    print(drop)


def _rest(args):
    pass


parser = argparse.ArgumentParser(prog=__file__)
sub_parsers = parser.add_subparsers()

add_parser = sub_parsers.add_parser("add")
add_parser.add_argument("message", metavar="M", type=str, nargs="+")
add_parser.set_defaults(func=_add)

list_parser = sub_parsers.add_parser("list")
list_parser.add_argument("--full", "-f", dest="full", action="store_true", default=False)
list_parser.set_defaults(func=_list)
list_parser.add_argument("--tag", "-t", dest="tags", action="append", default=[])
list_parser.add_argument("--limit", "-l", dest="limit", type=int, default=5)

get_parser = sub_parsers.add_parser("get")
get_parser.set_defaults(func=_get)
get_parser.add_argument("id", metavar="ID", type=str)


rest_parser = sub_parsers.add_parser("rest")
rest_parser.set_defualts(func=_rest)


if __name__ == "__main__":
    args = parser.parse_args()
    args.func(args)
