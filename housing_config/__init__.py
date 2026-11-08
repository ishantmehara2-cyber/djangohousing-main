import pymysql
from django.template.context import BaseContext

pymysql.install_as_MySQLdb()

# Python 3.14 + Django 5.1 compatibility patch for Context shallow copying
_orig_base_copy = BaseContext.__copy__

def _patched_base_copy(self):
    dup = _orig_base_copy(self)
    dup.__dict__.update(self.__dict__)
    return dup

BaseContext.__copy__ = _patched_base_copy
