#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: SELECT 1000 rows (async)
Benchmark selecting 1000 rows using async connection.
"""

import pytest
from conftest import get_async_cursor


SQL = "SELECT seq, 'abcdefghijabcdefghijabcdefghijaa' FROM seq_1_to_1000"


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=1000, warmup_rounds=100)
async def test_select_1000_rows_async(async_benchmark, async_connection, driver_name, setup_database, capture_benchmark_result):
    """Benchmark SELECT 1000 rows using async connection."""
    
    async def select_1000_rows():
        async with get_async_cursor(async_connection, driver_name) as cursor:
            if driver_name in ['async-mariadb']:
                await cursor.execute(SQL + " WHERE 1 = ?", (1,))
            else:  # mysql_connector_async, asyncmy
                await cursor.execute(SQL + " WHERE 1 = %s", (1,))
            rows = await cursor.fetchall()
            return len(rows)
    
    result = await async_benchmark(select_1000_rows)
    return capture_benchmark_result(result)
