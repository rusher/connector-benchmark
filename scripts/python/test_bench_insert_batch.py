#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: Batch INSERT
Benchmark batch insert operations with 100 rows.
"""

import pytest
import random
import string


chars = [ "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "\\Z", "😎", "🌶", "🎤", "🥂" ]

def randomString(length):
    result = "";
    for value in range(length):
        result = result + chars[random.randint(0, (len(chars) - 1))]
    return result;


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=200, warmup_rounds=50)
@pytest.mark.usefixtures("setup_database")
async def test_insert_batch(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark batch insert of 100 rows."""
    s = randomString(100)
    vals = [(s,) for i in range(100)]

    async def insert_batch():
        cursor = connection.cursor()
        
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            # Use executemany
            cursor.executemany("INSERT INTO perfTestTextBatch(t0) VALUES (?)",
                               vals)
        else:  # pymysql
            # Use executemany with %s
            cursor.executemany("INSERT INTO perfTestTextBatch(t0) VALUES (%s)",
                               vals)        
        cursor.close()
    
    result = await async_benchmark(insert_batch)
    return capture_benchmark_result(result)
