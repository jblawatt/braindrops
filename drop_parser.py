# coding: utf-8

import re
import importlib

from datetime import datetime


__all__ = [
        'TagParser',
        'AttrParser',
        'BirthdayAttrParser',
        'DropParserManager']


def get_type(dotted_path):
    mod_name, class_name = dotted_path.rsplit(".")
    mod = importlib.import_module(mod_name)
    return getattr(mod, class_name)


def _type_or_value(value):
    if isinstance(value, str):
        return get_type(value)
    else:
        return value


class TagParser(object):

    regex = re.compile("#(\w+)")

    def parse(self, drop):
        for tag in self.regex.findall(drop['original']):
            drop['tags'].append(tag)
        return drop


class AttrParser(object):

    def __init__(self):
        self.regex = re.compile("@{}:([\w\-\_\.]+)".format(self.attr_name))

    def parse_value(self, value):
        return value

    def parse(self, drop):
        for value in self.regex.findall(drop['original']):
            drop['attrs'][self.attr_name] = self.parse_value(value)
        return drop


class BirthdayAttrParser(AttrParser):

    attr_name = "bday"

    def parse_value(self, value):
        return datetime.strptime(value, "%d.%m.%Y").date()


class DropParserManager(object):

    def __init__(self, parser_types):


        self._parser_types = map(_type_or_value, parser_types or [])
        self._parser = [p() for p in self._parser_types]

    def _initialize(self, message):
        return {
            'message': message,
            'original': message,
            'datetime': datetime.now(),
            'tags': list(),
            'attrs': dict()
        }

    def parse(self, message):
        drop = self._initialize(message)
        for parser in self._parser:
            drop = parser.parse(drop)
        drop['tags'] = list(set(drop['tags']))
        return drop

