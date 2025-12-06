#include <benchmark/benchmark.h>
#include <iostream>
#include <string>
#include <cstring>
#include <stdlib.h>
#include <stdio.h>
#include <sql.h>
#include <sqlext.h>

#define OPERATION_PER_SECOND_LABEL "nb operations per second"

std::string GetEnvironmentVariableOrDefault(const std::string& variable_name,
                                            const std::string& default_value)
{
    const char* value = getenv(variable_name.c_str());
    return value ? value : default_value;
}

const int MAX_THREAD = atoi(GetEnvironmentVariableOrDefault("TEST_DB_THREAD", "1").c_str());
std::string DB_PORT = GetEnvironmentVariableOrDefault("TEST_DB_PORT", "3306");
std::string DB_DATABASE = GetEnvironmentVariableOrDefault("TEST_DB_DATABASE", "bench");
std::string DB_USER = GetEnvironmentVariableOrDefault("TEST_DB_USER", "root");
std::string DB_HOST = GetEnvironmentVariableOrDefault("TEST_DB_HOST", "127.0.0.1");
std::string DB_PASSWORD = GetEnvironmentVariableOrDefault("TEST_DB_PASSWORD", "");

const std::string TYPE = "MariaDB ODBC";

#define check_error(handle, handle_type, msg) \
do { \
  SQLCHAR sqlstate[6], message[SQL_MAX_MESSAGE_LENGTH]; \
  SQLINTEGER native_error; \
  SQLSMALLINT length; \
  if (SQLGetDiagRec(handle_type, handle, 1, sqlstate, &native_error, message, sizeof(message), &length) == SQL_SUCCESS) { \
    fprintf(stderr, "%s: %s (%s)\n", msg, message, sqlstate); \
  } else { \
    fprintf(stderr, "%s\n", msg); \
  } \
  exit(1); \
} while(0)

struct ODBCConnection {
  SQLHENV env;
  SQLHDBC dbc;
  
  ODBCConnection() {
    // Allocate environment handle
    if (SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env) != SQL_SUCCESS) {
      fprintf(stderr, "Failed to allocate environment handle\n");
      exit(1);
    }
    
    // Set ODBC version
    if (SQLSetEnvAttr(env, SQL_ATTR_ODBC_VERSION, (SQLPOINTER)SQL_OV_ODBC3, 0) != SQL_SUCCESS) {
      check_error(env, SQL_HANDLE_ENV, "Failed to set ODBC version");
    }
    
    // Allocate connection handle
    if (SQLAllocHandle(SQL_HANDLE_DBC, env, &dbc) != SQL_SUCCESS) {
      check_error(env, SQL_HANDLE_ENV, "Failed to allocate connection handle");
    }
    
    // Build connection string
    // Try environment variable first, then registered driver name, then direct path
    const char* driver_name = getenv("ODBC_DRIVER_NAME");
    std::string conn_str;
    
    if (driver_name) {
      // Use environment variable
      conn_str = "DRIVER={" + std::string(driver_name) + "};SERVER=" + DB_HOST + 
                 ";PORT=" + DB_PORT + ";DATABASE=" + DB_DATABASE + 
                 ";UID=" + DB_USER + ";PWD=" + DB_PASSWORD + ";";
    } else {
      // Try registered driver name first
      conn_str = "DRIVER={MariaDB ODBC};SERVER=" + DB_HOST + 
                 ";PORT=" + DB_PORT + ";DATABASE=" + DB_DATABASE + 
                 ";UID=" + DB_USER + ";PWD=" + DB_PASSWORD + ";";
    }
    
    // Connect to database
    SQLCHAR outstr[1024];
    SQLSMALLINT outstrlen;
    SQLRETURN ret = SQLDriverConnect(dbc, NULL, (SQLCHAR*)conn_str.c_str(), SQL_NTS,
                                     outstr, sizeof(outstr), &outstrlen, SQL_DRIVER_NOPROMPT);
    if (!SQL_SUCCEEDED(ret)) {
      check_error(dbc, SQL_HANDLE_DBC, "Failed to connect to database");
    }
  }
  
  ~ODBCConnection() {
    if (dbc) {
      SQLDisconnect(dbc);
      SQLFreeHandle(SQL_HANDLE_DBC, dbc);
    }
    if (env) {
      SQLFreeHandle(SQL_HANDLE_ENV, env);
    }
  }
};

// Benchmark: SELECT 1
static void BM_SELECT_1(benchmark::State& state) {
  ODBCConnection conn;
  SQLHSTMT stmt;
  
  for (auto _ : state) {
    SQLAllocHandle(SQL_HANDLE_STMT, conn.dbc, &stmt);
    
    SQLRETURN ret = SQLExecDirect(stmt, (SQLCHAR*)"SELECT 1", SQL_NTS);
    if (!SQL_SUCCEEDED(ret)) {
      check_error(stmt, SQL_HANDLE_STMT, "SELECT 1 failed");
    }
    
    SQLINTEGER result;
    SQLFetch(stmt);
    SQLGetData(stmt, 1, SQL_C_SLONG, &result, 0, NULL);
    
    SQLFreeHandle(SQL_HANDLE_STMT, stmt);
  }
  
  state.SetLabel(OPERATION_PER_SECOND_LABEL);
  state.counters["Type"] = benchmark::Counter(0, benchmark::Counter::kAvgIterations);
}
BENCHMARK(BM_SELECT_1)->Threads(MAX_THREAD)->UseRealTime();

// Note: DO 1 benchmark is not included for ODBC as the driver doesn't support DO statement

// Benchmark: SELECT 1000 rows - TEXT
static void BM_SELECT_1000_ROWS_TEXT(benchmark::State& state) {
  ODBCConnection conn;
  SQLHSTMT stmt;
  
  for (auto _ : state) {
    SQLAllocHandle(SQL_HANDLE_STMT, conn.dbc, &stmt);
    
    SQLRETURN ret = SQLExecDirect(stmt, (SQLCHAR*)"SELECT * FROM 1000rows WHERE 1 = 1", SQL_NTS);
    if (!SQL_SUCCEEDED(ret)) {
      check_error(stmt, SQL_HANDLE_STMT, "SELECT 1000 rows failed");
    }
    
    SQLBIGINT id;
    SQLCHAR val[101];
    while (SQLFetch(stmt) == SQL_SUCCESS) {
      SQLGetData(stmt, 1, SQL_C_SBIGINT, &id, 0, NULL);
      SQLGetData(stmt, 2, SQL_C_CHAR, val, sizeof(val), NULL);
    }
    
    SQLFreeHandle(SQL_HANDLE_STMT, stmt);
  }
  
  state.SetLabel(OPERATION_PER_SECOND_LABEL);
  state.counters["Type"] = benchmark::Counter(0, benchmark::Counter::kAvgIterations);
}
BENCHMARK(BM_SELECT_1000_ROWS_TEXT)->Threads(MAX_THREAD)->UseRealTime();

// Benchmark: SELECT 1000 rows - BINARY (prepared statement)
static void BM_SELECT_1000_ROWS_BINARY(benchmark::State& state) {
  ODBCConnection conn;
  SQLHSTMT stmt;
  
  SQLAllocHandle(SQL_HANDLE_STMT, conn.dbc, &stmt);
  
  // Prepare statement
  SQLRETURN ret = SQLPrepare(stmt, (SQLCHAR*)"SELECT * FROM 1000rows WHERE 1 = ?", SQL_NTS);
  if (!SQL_SUCCEEDED(ret)) {
    check_error(stmt, SQL_HANDLE_STMT, "Prepare SELECT 1000 rows failed");
  }
  
  SQLINTEGER param = 1;
  SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_SLONG, SQL_INTEGER, 0, 0, &param, 0, NULL);
  
  for (auto _ : state) {
    ret = SQLExecute(stmt);
    if (!SQL_SUCCEEDED(ret)) {
      check_error(stmt, SQL_HANDLE_STMT, "Execute SELECT 1000 rows failed");
    }
    
    SQLBIGINT id;
    SQLCHAR val[101];
    while (SQLFetch(stmt) == SQL_SUCCESS) {
      SQLGetData(stmt, 1, SQL_C_SBIGINT, &id, 0, NULL);
      SQLGetData(stmt, 2, SQL_C_CHAR, val, sizeof(val), NULL);
    }
    
    SQLCloseCursor(stmt);
  }
  
  SQLFreeHandle(SQL_HANDLE_STMT, stmt);
  
  state.SetLabel(OPERATION_PER_SECOND_LABEL);
  state.counters["Type"] = benchmark::Counter(1, benchmark::Counter::kAvgIterations);
}
BENCHMARK(BM_SELECT_1000_ROWS_BINARY)->Threads(MAX_THREAD)->UseRealTime();

// Benchmark: SELECT 100 int cols - TEXT
static void BM_SELECT_100_INT_TEXT(benchmark::State& state) {
  ODBCConnection conn;
  SQLHSTMT stmt;
  
  for (auto _ : state) {
    SQLAllocHandle(SQL_HANDLE_STMT, conn.dbc, &stmt);
    
    SQLRETURN ret = SQLExecDirect(stmt, (SQLCHAR*)"SELECT * FROM test100", SQL_NTS);
    if (!SQL_SUCCEEDED(ret)) {
      check_error(stmt, SQL_HANDLE_STMT, "SELECT 100 int cols failed");
    }
    
    SQLINTEGER values[100];
    if (SQLFetch(stmt) == SQL_SUCCESS) {
      for (int i = 0; i < 100; i++) {
        SQLGetData(stmt, i + 1, SQL_C_SLONG, &values[i], 0, NULL);
      }
    }
    
    SQLFreeHandle(SQL_HANDLE_STMT, stmt);
  }
  
  state.SetLabel(OPERATION_PER_SECOND_LABEL);
  state.counters["Type"] = benchmark::Counter(0, benchmark::Counter::kAvgIterations);
}
BENCHMARK(BM_SELECT_100_INT_TEXT)->Threads(MAX_THREAD)->UseRealTime();

// Benchmark: SELECT 100 int cols - BINARY (prepared statement)
static void BM_SELECT_100_INT_BINARY(benchmark::State& state) {
  ODBCConnection conn;
  SQLHSTMT stmt;
  
  SQLAllocHandle(SQL_HANDLE_STMT, conn.dbc, &stmt);
  
  SQLRETURN ret = SQLPrepare(stmt, (SQLCHAR*)"SELECT * FROM test100", SQL_NTS);
  if (!SQL_SUCCEEDED(ret)) {
    check_error(stmt, SQL_HANDLE_STMT, "Prepare SELECT 100 int cols failed");
  }
  
  for (auto _ : state) {
    ret = SQLExecute(stmt);
    if (!SQL_SUCCEEDED(ret)) {
      check_error(stmt, SQL_HANDLE_STMT, "Execute SELECT 100 int cols failed");
    }
    
    SQLINTEGER values[100];
    if (SQLFetch(stmt) == SQL_SUCCESS) {
      for (int i = 0; i < 100; i++) {
        SQLGetData(stmt, i + 1, SQL_C_SLONG, &values[i], 0, NULL);
      }
    }
    
    SQLCloseCursor(stmt);
  }
  
  SQLFreeHandle(SQL_HANDLE_STMT, stmt);
  
  state.SetLabel(OPERATION_PER_SECOND_LABEL);
  state.counters["Type"] = benchmark::Counter(1, benchmark::Counter::kAvgIterations);
}
BENCHMARK(BM_SELECT_100_INT_BINARY)->Threads(MAX_THREAD)->UseRealTime();

// Note: DO 1000 params and batch insert benchmarks are not included for ODBC

BENCHMARK_MAIN();
