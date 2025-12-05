#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: DO 1
Simple command execution benchmark.
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=10000, warmup_rounds=1000)
async def test_do_1(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark DO 1 command execution."""
    
    async def do_1():
        cursor = connection.cursor()
        cursor.execute("DO 1")
        cursor.close()
    
    result = await async_benchmark(do_1)
    return capture_benchmark_result(result)
