#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: SELECT 100 columns
Benchmark fetching a row with 100 integer columns.
"""

import pytest


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=1000, warmup_rounds=100)
@pytest.mark.usefixtures("setup_database")
async def test_select_100_cols_text(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark SELECT 100 columns using text protocol."""
    
    async def select_100_cols():
        cursor = connection.cursor()
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            cursor.execute("SELECT * FROM test100 WHERE 1 = ?", (1,))
        else:  # pymysql, mysql_connector
            cursor.execute("SELECT * FROM test100 WHERE 1 = %s", (1,))
        row = cursor.fetchone()
        cursor.close()
        return len(row)
    
    result = await async_benchmark(select_100_cols)
    return capture_benchmark_result(result)


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=100, warmup_rounds=10)
@pytest.mark.usefixtures("setup_database")
async def test_select_100_cols_binary(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark SELECT 100 columns using binary protocol (prepared statement)."""
    
    # Skip for drivers that don't support binary protocol
    if driver_name in ['pymysql', 'mysql_connector']:
        pytest.skip(f"{driver_name} doesn't support binary protocol")
    
    cursor = connection.cursor(binary=True)
    async def select_100_cols():
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            cursor.execute("SELECT * FROM test100 WHERE 1 = ?", (1,))
        else:  # pymysql, mysql_connector
            cursor.execute("SELECT * FROM test100 WHERE 1 = %s", (1,))
        row = cursor.fetchone()
        return len(row)
    
    result = await async_benchmark(select_100_cols)
    cursor.close()
    return capture_benchmark_result(result)
