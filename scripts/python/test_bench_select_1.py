#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: SELECT 1
Simple SELECT query benchmark.
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=10000, warmup_rounds=1000)
async def test_select_1(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark SELECT 1 query execution."""
    
    async def select_1():
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        rows = cursor.fetchall()
        del rows
        cursor.close()
    
    result = await async_benchmark(select_1)
    return capture_benchmark_result(result)
