#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark: SELECT 1 with connection pool
Test concurrent SELECT 1 queries using a connection pool with 16 connections
and 100 concurrent tasks.
"""

# Apply gevent monkey patching before any other imports
#from gevent import monkey
#monkey.patch_all()

import pytest
import os
import gevent
from gevent.pool import Pool


# Pool configuration
POOL_SIZE = 64
NUM_TASKS = 500


def get_pool(driver_name):
    """Create a connection pool using DBUtils PooledDB for all drivers."""
    try:
        from dbutils.pooled_db import PooledDB
    except ImportError:
        pytest.skip("DBUtils not installed")
    
    db_config = {
        'host': os.getenv('TEST_DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('TEST_DB_PORT', '3306')),
        'user': os.getenv('TEST_DB_USER', 'root'),
        'password': os.getenv('TEST_DB_PASSWORD', ''),
        'database': os.getenv('TEST_DB_DATABASE', 'bench')
    }
    
    # Import the appropriate driver module
    if driver_name == 'mariadb' or driver_name == 'mariadb_c':
        import mariadb as driver_module
    elif driver_name == 'pymysql':
        import pymysql as driver_module
    elif driver_name == 'mysql_connector':
        import mysql.connector as driver_module
    else:
        pytest.skip(f"Unknown driver: {driver_name}")
    
    # Create pool with consistent configuration
    pool = PooledDB(
        creator=driver_module,
        maxconnections=POOL_SIZE,
        mincached=POOL_SIZE,
        maxcached=POOL_SIZE,
        blocking=True,
        **db_config
    )
    return pool


def execute_select_1(pool, driver_name):
    """Execute SELECT 1 using a connection from the pool."""
    # PooledDB uses .connection() method for all drivers
    conn = pool.connection()
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        return result[0]
    finally:
        conn.close()


@pytest.mark.asyncio
@pytest.mark.async_benchmark(rounds=100, warmup_rounds=10)
async def test_select_1_pool(async_benchmark, driver_name, capture_benchmark_result):
    """Benchmark SELECT 1 with connection pool using gevent greenlets for true cooperative concurrency."""
    
    db_pool = get_pool(driver_name)
    
    async def run_concurrent_selects():
        # Use gevent's Pool for cooperative concurrency
        gevent_pool = Pool(NUM_TASKS)
        
        # Spawn greenlets to execute queries concurrently
        greenlets = [gevent_pool.spawn(execute_select_1, db_pool, driver_name) for _ in range(NUM_TASKS)]
        
        # Wait for all greenlets to complete
        gevent.joinall(greenlets)
        
        return NUM_TASKS
    
    result = await async_benchmark(run_concurrent_selects)
    del db_pool
    
    return capture_benchmark_result(result)
