#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: SELECT 1000 rows
Benchmark fetching 1000 rows with text and binary protocol.
"""

import pytest


SQL = "SELECT seq, 'abcdefghijabcdefghijabcdefghijaa' FROM seq_1_to_1000"


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=100, warmup_rounds=10)
async def test_select_1000_rows_text(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark SELECT 1000 rows using text protocol (regular execute)."""
    
    async def select_1000_rows():
        cursor = connection.cursor()
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            cursor.execute(SQL + " WHERE 1 = ?", (1,))
        else:  # pymysql, mysql_connector
            cursor.execute(SQL + " WHERE 1 = %s", (1,))
        rows = cursor.fetchall()
        cursor.close()
        return len(rows)
    
    result = await async_benchmark(select_1000_rows)
    return capture_benchmark_result(result)


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=1000, warmup_rounds=100)
async def test_select_1000_rows_binary(async_benchmark, connection, driver_name, capture_benchmark_result):
    """Benchmark SELECT 1000 rows using binary protocol (prepared statement)."""
    
    # Skip for drivers that don't support binary protocol
    if driver_name in ['pymysql', 'mysql_connector']:
        pytest.skip(f"{driver_name} doesn't support binary protocol")
    
    
    async def select_1000_rows():
        cursor = connection.cursor(binary=True)
        if driver_name == 'mariadb' or driver_name == 'mariadb_c':
            cursor.execute(SQL + " WHERE 1 = ?", (1,))
        else:  # pymysql, mysql_connector
            cursor.execute(SQL + " WHERE 1 = %s", (1,))
        rows = cursor.fetchall()
        cursor.close()
        return len(rows)
    
    result = await async_benchmark(select_1000_rows)
    return capture_benchmark_result(result)
