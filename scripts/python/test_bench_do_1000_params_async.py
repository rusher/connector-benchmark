#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: DO 1000 parameters (async)
Benchmark executing DO with 1000 parameters using async connection.
"""

import pytest
from conftest import get_async_cursor


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=1000, warmup_rounds=100)
async def test_do_1000_params_async(async_benchmark, async_connection, driver_name, capture_benchmark_result):
    """Benchmark DO with 1000 parameters using async connection."""
    
    # Build query with 1000 parameters - use correct placeholder for driver
    if driver_name == 'async-mariadb':
        placeholders = ','.join(['?' for _ in range(1000)])
    else:  # mysql_connector_async, asyncmy use %s
        placeholders = ','.join(['%s' for _ in range(1000)])
    
    query = f"DO {placeholders}"
    params = tuple(range(1000))
    
    async def do_1000_params():
        async with get_async_cursor(async_connection, driver_name) as cursor:
            await cursor.execute(query, params)
    
    result = await async_benchmark(do_1000_params)
    return capture_benchmark_result(result)
