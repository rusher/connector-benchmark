#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: SELECT 100 columns (async)
Benchmark selecting 100 integer columns using async connection.
"""

import pytest
from conftest import get_async_cursor


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=1000, warmup_rounds=100)
async def test_select_100_cols_async(async_benchmark, async_connection, driver_name, setup_database, capture_benchmark_result):
    """Benchmark SELECT 100 int columns using async connection."""
    
    async def select_100_cols():
        async with get_async_cursor(async_connection, driver_name) as cursor:
            await cursor.execute("SELECT * FROM test100")
            row = await cursor.fetchone()
            return len(row)
    
    result = await async_benchmark(select_100_cols)
    return capture_benchmark_result(result)
