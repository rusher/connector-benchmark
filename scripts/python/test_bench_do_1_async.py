#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: DO 1 (async)
Simple benchmark executing "DO 1" using async connection.
"""

import pytest
from conftest import get_async_cursor


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=10000, warmup_rounds=1000)
async def test_do_1_async(async_benchmark, async_connection, driver_name, capture_benchmark_result):
    """Benchmark DO 1 using async connection."""
    
    async def do_1():
        async with get_async_cursor(async_connection, driver_name) as cursor:
            await cursor.execute("DO 1")
    
    result = await async_benchmark(do_1)
    return capture_benchmark_result(result)
