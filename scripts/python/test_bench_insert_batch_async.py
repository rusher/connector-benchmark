#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: Batch INSERT (async)
Benchmark batch inserting 100 rows using async connection.
"""

import pytest
from conftest import get_async_cursor


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=200, warmup_rounds=50)
async def test_insert_batch_async(async_benchmark, async_connection, driver_name, setup_database, capture_benchmark_result):
    """Benchmark batch INSERT of 100 rows using async connection."""
    
    # Prepare data
    data = [('a' * 100,) for _ in range(100)]
    
    async def insert_batch():
        async with get_async_cursor(async_connection, driver_name) as cursor:
            await cursor.execute("TRUNCATE TABLE perfTestTextBatch")
            if driver_name == 'async-mariadb':
                await cursor.executemany("INSERT INTO perfTestTextBatch(t0) VALUES (?)", data)
            else:  # mysql_connector_async, asyncmy use %s
                await cursor.executemany("INSERT INTO perfTestTextBatch(t0) VALUES (%s)", data)
            return cursor.rowcount
    
    result = await async_benchmark(insert_batch)
    return capture_benchmark_result(result)
