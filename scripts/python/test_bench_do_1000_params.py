#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: DO with 1000 parameters
Benchmark parameter binding with many parameters.
"""

import pytest


# Build SQL with 1000 parameters
SQL = "DO " + ",".join(["?" if i == 0 else "?" for i in range(1000)])
SQL_PERCENT = "DO " + ",".join(["%s" for _ in range(1000)])


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=100, warmup_rounds=10)
async def test_do_1000_params_text(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark DO with 1000 parameters using text protocol."""
    
    params = list(range(1, 1001))
    
    cursor = connection.cursor()
    async def do_1000_params():
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            cursor.execute(SQL, params)
        else:  # pymysql
            cursor.execute(SQL_PERCENT, params)
    
    result = await async_benchmark(do_1000_params)
    cursor.close()
    return capture_benchmark_result(result)

@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=1000, warmup_rounds=100)
async def test_do_1000_params_binary(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark DO with 1000 parameters using binary protocol."""
    
    # Skip for drivers that don't support binary protocol
    if driver_name in ['pymysql', 'mysql_connector']:
        pytest.skip(f"{driver_name} doesn't support binary protocol")

    params = list(range(1, 1001))
    
    async def do_1000_params():
        cursor = connection.cursor(binary=True)
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            cursor.execute(SQL, params)
        else:  # pymysql
            cursor.execute(SQL_PERCENT, params)
        cursor.close()
    
    result = await async_benchmark(do_1000_params)
    return capture_benchmark_result(result)
