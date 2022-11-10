#!/usr/bin/env python -O
# -*- coding: utf-8 -*-

import os


def glob():
    dm = {
        "module": os.environ.get('TEST_MODULE', 'mariadb'),
        }

    return dm


def conf():
    d = {
        "user": os.environ.get('TEST_DB_USER', 'root'),
        "host": os.environ.get('TEST_DB_HOST', '127.0.0.1'),
        "database": os.environ.get('TEST_DB_DATABASE', 'bench'),
        "port": int(os.environ.get('TEST_DB_PORT', '3306')),
    }
    if os.environ.get('TEST_DB_PASSWORD'):
        d["password"] = os.environ.get('TEST_DB_PASSWORD')
    if os.environ.get('TEST_USE_SSL', 'false')  == "true":
        d["ssl"] = True

    return d
