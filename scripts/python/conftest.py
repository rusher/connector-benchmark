#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2012-2014 Monty Program Ab
# Copyright (c) 2015-2025 MariaDB Corporation Ab

"""
Benchmark configuration and fixtures for comparing mariadb, mariadb_c, and pymysql.
"""

import os
import sys
import pytest
import pytest_asyncio
from contextlib import asynccontextmanager


# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('TEST_DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('TEST_DB_PORT', '3306')),
    'user': os.environ.get('TEST_DB_USER', 'root'),
    'password': os.environ.get('TEST_DB_PASSWORD', ''),
    'database': os.environ.get('TEST_DB_DATABASE', 'testp'),
}

# Global variable to store mysql_connector implementation type
_mysql_connector_impl = None


def get_driver_module(driver_name):
    """Import and return the specified driver module."""
    if driver_name in ['mariadb', 'mariadb_c']:
        # Environment variable is already set by run_benchmarks.py
        import mariadb
        print(f"\n{driver_name} using implementation: {mariadb.__impl__}")
        return mariadb
    elif driver_name == 'async-mariadb':
        import mariadb
        print(f"\n{driver_name} using async implementation")
        return mariadb
    elif driver_name == 'mysql_connector_async':
        import mysql.connector.aio
        print(f"\n{driver_name} using async implementation")
        return mysql.connector.aio
    elif driver_name == 'asyncmy':
        import asyncmy
        print(f"\n{driver_name} using async implementation")
        return asyncmy
    elif driver_name == 'pymysql':
        import pymysql
        return pymysql
    elif driver_name == 'mysql_connector':
        global _mysql_connector_impl
        import mysql.connector
        # Detect if using C extension or pure Python implementation
        # The C extension module is _mysql_connector
        try:
            import _mysql_connector
            from mysql.connector.connection_cext import CMySQLConnection
            _mysql_connector_impl = "C"
            impl_type = "C extension (CMySQLConnection)"
        except ImportError:
            _mysql_connector_impl = "Python"
            impl_type = "pure Python (MySQLConnection)"
        print(f"\n{driver_name} using implementation: {impl_type}")
        print(f"Note: mysql-connector-python C extension is slower than mariadb-connector-python C implementation")
        return mysql.connector
    else:
        raise ValueError(f"Unknown driver: {driver_name}")


def _get_driver_ids():
    """Generate driver IDs for parametrization, detecting mysql_connector implementation type."""
    global _mysql_connector_impl
    
    # Detect mysql_connector implementation type early
    if _mysql_connector_impl is None:
        try:
            import mysql.connector
            # Create a test connection to see which implementation is actually used
            # Check the default connection class
            test_config = {'host': 'localhost', 'user': 'root'}
            try:
                # Try to determine from connection class without actually connecting
                # Check if CMySQLConnection is available and will be used by default
                from mysql.connector.connection_cext import CMySQLConnection
                _mysql_connector_impl = "C"
            except ImportError:
                _mysql_connector_impl = "Python"
        except Exception:
            # Fallback: check if _mysql_connector module exists
            try:
                import _mysql_connector
                _mysql_connector_impl = "C"
            except ImportError:
                _mysql_connector_impl = "Python"
    
    ids = ['mariadb', 'mariadb_c', 'async-mariadb', 'pymysql']
    if _mysql_connector_impl:
        ids.append(f'mysql_connector ({_mysql_connector_impl})')
    else:
        ids.append('mysql_connector')
    ids.append('mysql_connector_async')
    ids.append('asyncmy')
    
    return ids


@pytest.fixture(scope='session', params=['mariadb', 'mariadb_c', 'async-mariadb', 'pymysql', 'mysql_connector', 'mysql_connector_async', 'asyncmy'], ids=_get_driver_ids())
def driver_name(request):
    """Parametrize tests across all drivers."""
    return request.param


@pytest.fixture(scope='session')
def driver(driver_name):
    """Get the driver module for the current test."""
    # Extract base driver name (remove implementation type suffix if present)
    base_name = driver_name.split(' (')[0] if ' (' in driver_name else driver_name
    return get_driver_module(base_name)


_driver_warmed_up = {}

@pytest.fixture(scope='session', autouse=True)
def warmup_session(driver, driver_name):
    """Warm up the database and driver once per session, automatically before any tests run."""
    # Skip warmup for async drivers as they require async/await
    if driver_name in ['async-mariadb', 'mysql_connector_async', 'asyncmy']:
        return
    
    driver_key = id(driver)
    if driver_key not in _driver_warmed_up:
        # Create a temporary connection just for warmup
        warmup_conn = driver.connect(**DB_CONFIG)
        warmup_cursor = warmup_conn.cursor()
        
        # Warm up with simple queries (simulates running test_do_1 first)
        for _ in range(6000):
            warmup_cursor.execute("DO 1")
        
        # Also warm up cursor creation/destruction pattern
        warmup_cursor.close()
        for _ in range(6000):
            warmup_cursor = warmup_conn.cursor()
            warmup_cursor.execute("SELECT seq, 'abcdefghijabcdefghijabcdefghijaa' FROM seq_1_to_1000")
            warmup_cursor.fetchall()
            warmup_cursor.close()
        
        warmup_conn.close()
        _driver_warmed_up[driver_key] = True


@pytest.fixture(scope='function')
def connection(driver, driver_name):
    """Create a database connection for each test."""
    # Skip async drivers for sync tests
    if driver_name in ['async-mariadb', 'mysql_connector_async', 'asyncmy']:
        pytest.skip(f"{driver_name} requires async tests")
    
    # Now create the actual test connection
    conn = driver.connect(**DB_CONFIG)
    yield conn
    try:
        conn.close()
    except:
        pass


@asynccontextmanager
async def get_async_cursor(connection, driver_name):
    """Helper to get async cursor handling different APIs."""
    if driver_name == 'mysql_connector_async':
        # mysql.connector.aio requires await for cursor()
        cursor = await connection.cursor()
        try:
            yield cursor
        finally:
            await cursor.close()
    else:
        # mariadb and asyncmy support async context manager
        async with connection.cursor() as cursor:
            yield cursor


@pytest_asyncio.fixture(scope='function')
async def async_connection(driver, driver_name):
    """Create an async database connection for each test."""
    # Only async drivers use this fixture
    if driver_name not in ['async-mariadb', 'mysql_connector_async', 'asyncmy']:
        pytest.skip(f"{driver_name} doesn't support async")
    
    if driver_name == 'async-mariadb':
        import mariadb
        conn = await mariadb.asyncConnect(**DB_CONFIG)
    elif driver_name == 'mysql_connector_async':
        import mysql.connector.aio
        conn = await mysql.connector.aio.connect(**DB_CONFIG)
    elif driver_name == 'asyncmy':
        import asyncmy
        conn = await asyncmy.connect(**DB_CONFIG)
    
    yield conn
    try:
        await conn.close()
    except:
        pass


@pytest.fixture(scope='session')
def setup_database():
    """Setup test database tables once per session."""
    # Use mariadb for setup (doesn't matter which driver)
    os.environ['MARIADB_PYTHON_CONNECTOR'] = 'python'
    import mariadb
    
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Install BLACKHOLE engine if available
        try:
            cursor.execute("INSTALL SONAME 'ha_blackhole'")
        except:
            pass
        
        # Create test100 table (100 integer columns)
        cursor.execute("DROP TABLE IF EXISTS test100")
        cols = ",".join([f"i{i} int" for i in range(1, 101)])
        table_sql = f"CREATE TABLE test100 ({cols})"
        try:
            cursor.execute(table_sql + " ENGINE = MEMORY")
        except:
            cursor.execute(table_sql)
        vals = ",".join([str(i) for i in range(1, 101)])
        cursor.execute(f"INSERT INTO test100 VALUES ({vals})")
        
        # Warm up the test100 table by accessing it multiple times
        for _ in range(100):
            cursor.execute("SELECT * FROM test100")
            cursor.fetchone()
        
        # Create perfTestTextBatch table
        cursor.execute("DROP TABLE IF EXISTS perfTestTextBatch")
        create_table = (
            "CREATE TABLE perfTestTextBatch ("
            "id MEDIUMINT NOT NULL AUTO_INCREMENT, "
            "t0 text, "
            "PRIMARY KEY (id)"
            ") COLLATE='utf8mb4_unicode_ci'"
        )
        try:
            cursor.execute(create_table + " ENGINE = BLACKHOLE")
        except:
            cursor.execute(create_table)
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    
    yield
    
    # Cleanup after all tests
    conn = mariadb.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS test100")
        cursor.execute("DROP TABLE IF EXISTS perfTestTextBatch")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# Store async benchmark results for JSON export
_async_benchmark_results = {}


@pytest.fixture
def capture_benchmark_result(request):
    """Fixture to capture and store benchmark results."""
    def capture(result):
        if isinstance(result, dict) and ('mean' in result or 'times' in result):
            print(f"\nDEBUG: Capturing result for {request.node.nodeid}")
            _async_benchmark_results[request.node.nodeid] = {
                'nodeid': request.node.nodeid,
                'name': request.node.name,
                'results': result
            }
        return result
    return capture


def pytest_sessionfinish(session, exitstatus):
    """Save async benchmark results to JSON file compatible with pytest-benchmark."""
    import json
    import platform
    from pathlib import Path
    import sys
    import statistics
    import time
    
    print(f"\nDEBUG: pytest_sessionfinish called")
    print(f"DEBUG: _async_benchmark_results has {len(_async_benchmark_results)} entries")
    
    # Try to get the JSON output path from command line
    json_path = None
    for i, arg in enumerate(sys.argv):
        if arg == '--benchmark-json' and i + 1 < len(sys.argv):
            json_path = sys.argv[i + 1]
            break
    
    print(f"DEBUG: JSON path: {json_path}")
    
    if not json_path:
        print("DEBUG: No JSON path found, returning")
        return
    
    # Only process if we have async results
    if not _async_benchmark_results:
        print("DEBUG: No benchmark results to save")
        return
    
    # Create pytest-benchmark compatible structure
    benchmarks = []
    for nodeid, result_data in _async_benchmark_results.items():
        results = result_data.get('results', {})
        
        # Extract timing data from results
        if isinstance(results, dict):
            times = results.get('times', [])
            mean_time = results.get('mean', 0)
            min_time = results.get('min', 0)
            max_time = results.get('max', 0)
            median_time = results.get('median', 0)
            stddev_time = results.get('stddev', 0)
            rounds = results.get('rounds', 100)
        else:
            # Fallback
            times = []
            mean_time = min_time = max_time = median_time = stddev_time = 0
            rounds = 100
        
        if mean_time > 0 or times:
            if not times and mean_time > 0:
                # Use mean if we have it but not times array
                times = [mean_time] * rounds
            
            benchmark_data = {
                'name': result_data['name'],
                'fullname': nodeid,
                'params': {},
                'stats': {
                    'min': min_time if min_time > 0 else (min(times) if times else 0),
                    'max': max_time if max_time > 0 else (max(times) if times else 0),
                    'mean': mean_time if mean_time > 0 else (statistics.mean(times) if times else 0),
                    'median': median_time if median_time > 0 else (statistics.median(times) if times else 0),
                    'stddev': stddev_time if stddev_time > 0 else (statistics.stdev(times) if len(times) > 1 else 0),
                    'rounds': rounds if rounds > 0 else len(times),
                    'iterations': 1,
                }
            }
            benchmarks.append(benchmark_data)
    
    if benchmarks:
        output = {
            'machine_info': {
                'node': platform.node(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'python_implementation': platform.python_implementation(),
                'python_version': platform.python_version(),
            },
            'commit_info': {},
            'benchmarks': benchmarks,
            'datetime': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'version': '1.0.0'
        }
        
        # Save to file
        output_path = Path(json_path)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
