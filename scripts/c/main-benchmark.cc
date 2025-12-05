#include <benchmark/benchmark.h>
#include <iostream>
#include <string>
#include <cstring>
#include <stdlib.h>
#include <stdio.h>

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
bool DB_SSL = GetEnvironmentVariableOrDefault("TEST_USE_SSL", "false") == "true";

#define check_conn_rc(rc, mysql) \
do {\
  if (rc)\
  {\
    fprintf(stdout,"Error (%d): %s (%d) in %s line %d", rc, mysql_error(mysql), \
         mysql_errno(mysql), __FILE__, __LINE__);\
    mysql_close(conn);\
    exit(1);\
  }\
} while(0)


#define check_stmt_rc(rc, stmt, mysql) \
do {\
  if (rc)\
  {\
    fprintf(stdout,"Error (%d): %d (%s) in %s line %d", rc,  mysql_stmt_errno(stmt), \
         mysql_stmt_error(stmt), __FILE__, __LINE__);\
    mysql_close(conn);\
    exit(1);\
  }\
} while(0)

#ifndef BENCHMARK_MYSQL
#include <mysql.h>
const std::string TYPE = "MariaDB";

MYSQL* connect(std::string options) {
  MYSQL *con = mysql_init(NULL);
   if (!(con = mysql_init(0))) {
    fprintf(stderr, "unable to initialize connection struct\n");
    exit(1);
   }

  enum mysql_protocol_type prot_type= MYSQL_PROTOCOL_TCP;
  mysql_optionsv(con, MYSQL_OPT_PROTOCOL, (void *)&prot_type);
  if (DB_SSL) {
    mysql_ssl_set(con,
                  NULL,
                  NULL,
                  NULL,
                  NULL,
                  NULL);
  } else {
    my_bool zero = false;
    mysql_optionsv(con, MYSQL_OPT_SSL_ENFORCE, &zero);
    mysql_options(con,MYSQL_OPT_SSL_VERIFY_SERVER_CERT,&zero);
  }

  if (mysql_real_connect(con, DB_HOST.c_str(), DB_USER.c_str(), DB_PASSWORD.c_str(),
          DB_DATABASE.c_str(), atoi(DB_PORT.c_str()), NULL, 0) == NULL) {
    fprintf(stderr, "%s\n", mysql_error(con));
    mysql_close(con);
    exit(1);
  }
  return con;
}
#endif

#ifdef BENCHMARK_MYSQL
    #include <mysql/mysql.h>
const std::string TYPE = "MySQL";

MYSQL* connect(std::string options) {
  MYSQL *con = mysql_init(NULL);

  if (con == NULL) {
      fprintf(stderr, "%s\n", mysql_error(con));
      exit(1);
  }

  enum mysql_protocol_type prot_type= MYSQL_PROTOCOL_TCP;
  mysql_options(con, MYSQL_OPT_PROTOCOL, (void *)&prot_type);
  if (DB_SSL) {
    mysql_ssl_set(con,
                  NULL,
                  NULL,
                  NULL,
                  NULL,
                  NULL);
  } else {
    enum mysql_ssl_mode ssl_mode = SSL_MODE_DISABLED;
    mysql_options(con, MYSQL_OPT_SSL_MODE, &ssl_mode);
  }

  if (mysql_real_connect(con, DB_HOST.c_str(), DB_USER.c_str(), DB_PASSWORD.c_str(),
          DB_DATABASE.c_str(), atoi(DB_PORT.c_str()), NULL, 0) == NULL) {
      fprintf(stderr, "%s\n", mysql_error(con));
      mysql_close(con);
      exit(1);
  }

//  int rc;
//    rc = mysql_query(con, "show STATUS  LIKE 'Ssl_version'");
//
//    MYSQL_RES *result = mysql_store_result(con);
//
//    int val;
//    MYSQL_ROW row;
//    row = mysql_fetch_row(result);
//
//    fprintf(stderr, "----%s\n", row[1]);
//    mysql_free_result(result);

  return con;
}
#endif



void do_1(benchmark::State& state, MYSQL* conn) {
  int rc;
  rc = mysql_query(conn, "DO 1");
  check_conn_rc(rc, conn);

  int id;
  benchmark::DoNotOptimize(id = mysql_insert_id(conn));
}

static void BM_DO_1(benchmark::State& state) {
  MYSQL *conn = connect("");
  int numOperation = 0;
  for (auto _ : state) {
    do_1(state, conn);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_close(conn);
}

BENCHMARK(BM_DO_1)->Name(TYPE + " DO 1")->Threads(MAX_THREAD)->UseRealTime();




void select_1(benchmark::State& state, MYSQL* conn) {
  int rc;
  rc = mysql_query(conn, "SELECT 1");
  check_conn_rc(rc, conn);

  MYSQL_RES *result = mysql_store_result(conn);
  int num_fields = mysql_num_fields(result);

  char* val_name;
  MYSQL_FIELD *field;
  while(field = mysql_fetch_field(result)) {
    benchmark::DoNotOptimize(val_name = field->name);
  }

  int val;
  MYSQL_ROW row;
  while ((row = mysql_fetch_row(result))) {
    for(int i = 0; i < num_fields; i++) {
      benchmark::DoNotOptimize(val = atoi(row[i]));
    }
  }

  mysql_free_result(result);
}

static void BM_SELECT_1(benchmark::State& state) {
  MYSQL *conn = connect("");
  int numOperation = 0;
  for (auto _ : state) {
    select_1(state, conn);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_close(conn);
}

BENCHMARK(BM_SELECT_1)->Name(TYPE + " SELECT 1")->Threads(MAX_THREAD)->UseRealTime();



void select_1000_rows_text(benchmark::State& state, MYSQL* conn) {
    if (mysql_query(conn, "select * from 1000rows where 1 = 1")) {
          fprintf(stderr, "%s\n", mysql_error(conn));
          mysql_close(conn);
          exit(1);
    }
    MYSQL_RES *result = mysql_store_result(conn);
    unsigned int num_fields = mysql_num_fields(result);

    if (result == NULL) {
          fprintf(stderr, "%s\n", mysql_error(conn));
          mysql_close(conn);
          exit(1);
    }

    int val1;
    std::string val2;
    MYSQL_ROW row;
    while ((row = mysql_fetch_row(result))) {
        benchmark::DoNotOptimize(val1 = atoi(row[0]));
        benchmark::DoNotOptimize(val2 = row[1]);
        benchmark::ClobberMemory();
    }

    mysql_free_result(result);
}

void select_1000_rows_binary(benchmark::State& state, MYSQL_STMT* stmt, MYSQL_BIND* result_bind, int* val1, char* val2) {
    if (mysql_stmt_execute(stmt)) {
        fprintf(stderr, "%s\n", mysql_stmt_error(stmt));
        exit(1);
    }
    
    while (mysql_stmt_fetch(stmt) == 0) {
        benchmark::DoNotOptimize(*val1);
        benchmark::DoNotOptimize(val2);
        benchmark::ClobberMemory();
    }
}

static void BM_SELECT_1000_ROWS_TEXT(benchmark::State& state) {
  MYSQL *conn = connect("");
  int numOperation = 0;
  for (auto _ : state) {
    select_1000_rows_text(state, conn);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_close(conn);
}

static void BM_SELECT_1000_ROWS_BINARY(benchmark::State& state) {
  MYSQL *conn = connect("");
  
  // Prepare statement once before benchmark loop
  MYSQL_STMT *stmt = mysql_stmt_init(conn);
  if (!stmt) {
      fprintf(stderr, "mysql_stmt_init() failed\n");
      mysql_close(conn);
      exit(1);
  }
  
  const char* query = "select * from 1000rows where 1 = ?";
  if (mysql_stmt_prepare(stmt, query, strlen(query))) {
      fprintf(stderr, "%s\n", mysql_stmt_error(stmt));
      mysql_stmt_close(stmt);
      mysql_close(conn);
      exit(1);
  }
  
  MYSQL_BIND bind[1];
  int param_value = 1;
  memset(bind, 0, sizeof(bind));
  bind[0].buffer_type = MYSQL_TYPE_LONG;
  bind[0].buffer = (char *)&param_value;
  
  if (mysql_stmt_bind_param(stmt, bind)) {
      fprintf(stderr, "%s\n", mysql_stmt_error(stmt));
      mysql_stmt_close(stmt);
      mysql_close(conn);
      exit(1);
  }
  
  MYSQL_BIND result_bind[2];
  int val1;
  char val2[33];
  unsigned long val2_length;
#ifndef BENCHMARK_MYSQL
  my_bool val2_is_null;  // MariaDB uses my_bool
#else
  bool val2_is_null;     // MySQL 8.0+ uses bool
#endif
  
  memset(result_bind, 0, sizeof(result_bind));
  result_bind[0].buffer_type = MYSQL_TYPE_LONG;
  result_bind[0].buffer = (char *)&val1;
  result_bind[1].buffer_type = MYSQL_TYPE_STRING;
  result_bind[1].buffer = val2;
  result_bind[1].buffer_length = 33;
  result_bind[1].length = &val2_length;
  result_bind[1].is_null = &val2_is_null;
  
  if (mysql_stmt_bind_result(stmt, result_bind)) {
      fprintf(stderr, "%s\n", mysql_stmt_error(stmt));
      mysql_stmt_close(stmt);
      mysql_close(conn);
      exit(1);
  }
  
  // Benchmark loop - only execute and fetch
  int numOperation = 0;
  for (auto _ : state) {
    select_1000_rows_binary(state, stmt, result_bind, &val1, val2);
    numOperation++;
  }
  
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_stmt_close(stmt);
  mysql_close(conn);
}

BENCHMARK(BM_SELECT_1000_ROWS_TEXT)->Name(TYPE + " SELECT 1000 rows (int + char(32))")->Threads(MAX_THREAD)->UseRealTime();
BENCHMARK(BM_SELECT_1000_ROWS_BINARY)->Name(TYPE + " SELECT 1000 rows (int + char(32)) - BINARY")->Threads(MAX_THREAD)->UseRealTime();

void select_100_int_cols(benchmark::State& state, MYSQL* conn) {
    int rc;
    rc = mysql_query(conn, "select * FROM test100");
    check_conn_rc(rc, conn);

    MYSQL_RES *result = mysql_store_result(conn);
    unsigned int num_fields = mysql_num_fields(result);

    if (result == NULL) {
          fprintf(stderr, "%s\n", mysql_error(conn));
          mysql_close(conn);
          exit(1);
    }

    int val1;
    MYSQL_ROW row;
    while ((row = mysql_fetch_row(result))) {
        for (int i=0; i<100; i++)
            benchmark::DoNotOptimize(val1 = atoi(row[i]));
        benchmark::ClobberMemory();
    }

    mysql_free_result(result);
}

void select_100_int_cols_with_prepare(benchmark::State& state, MYSQL* conn) {
  MYSQL_STMT *stmt = mysql_stmt_init(conn);
  std::string query = "select * FROM test100";
  int rc;

  rc = mysql_stmt_prepare(stmt, query.c_str(), (unsigned long)query.size());
  check_conn_rc(rc, conn);

  int int_data[100];
  unsigned long length[100];

  MYSQL_BIND my_bind[100];
  memset(my_bind, 0, sizeof(my_bind));

  for (int i = 0; i < 100; i++) {
    my_bind[i].buffer_type= MYSQL_TYPE_LONG;
    my_bind[i].buffer= (char *) &int_data[i];
    my_bind[i].length= &length[i];
  }

  rc = mysql_stmt_execute(stmt);
  check_conn_rc(rc, conn);

  rc = mysql_stmt_bind_result(stmt, my_bind);
  check_stmt_rc(rc, stmt, conn);

  rc = mysql_stmt_store_result(stmt);
  check_stmt_rc(rc, stmt, conn);

  while (mysql_stmt_fetch(stmt)) {
    //
  }

  mysql_stmt_close(stmt);
}

void select_100_int_cols_prepared(benchmark::State& state, MYSQL* conn, MYSQL_STMT* stmt) {
  int rc;
  int int_data[100];
  unsigned long length[100];

  MYSQL_BIND my_bind[100];
  memset(my_bind, 0, sizeof(my_bind));

  for (int i = 0; i < 100; i++) {
    my_bind[i].buffer_type= MYSQL_TYPE_LONG;
    my_bind[i].buffer= (char *) &int_data[i];
    my_bind[i].length= &length[i];
  }

  rc = mysql_stmt_execute(stmt);
  check_conn_rc(rc, conn);

  rc = mysql_stmt_bind_result(stmt, my_bind);
  check_stmt_rc(rc, stmt, conn);

  rc = mysql_stmt_store_result(stmt);
  check_stmt_rc(rc, stmt, conn);

  while (mysql_stmt_fetch(stmt)) {
    //
  }
}

static void BM_SELECT_100_INT_COLS(benchmark::State& state) {
  MYSQL *conn = connect("");
  int numOperation = 0;
  for (auto _ : state) {
    select_100_int_cols(state, conn);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_close(conn);
}


static void BM_SELECT_100_INT_COLS_WITH_PREPARE(benchmark::State& state) {
  MYSQL *conn = connect("");
  int numOperation = 0;
  for (auto _ : state) {
    select_100_int_cols_with_prepare(state, conn);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_close(conn);
}

static void BM_SELECT_100_INT_COLS_PREPARED(benchmark::State& state) {
  MYSQL *conn = connect("");
  MYSQL_STMT *stmt = mysql_stmt_init(conn);
  std::string query = "select * FROM test100";
  int rc;

  rc = mysql_stmt_prepare(stmt, query.c_str(), (unsigned long)query.size());
  check_conn_rc(rc, conn);
  int numOperation = 0;
  for (auto _ : state) {
    select_100_int_cols_prepared(state, conn, stmt);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_stmt_close(stmt);
  mysql_close(conn);
}

BENCHMARK(BM_SELECT_100_INT_COLS)->Name(TYPE + " SELECT 100 int cols")->Threads(MAX_THREAD)->UseRealTime();
BENCHMARK(BM_SELECT_100_INT_COLS_WITH_PREPARE)->Name(TYPE + " SELECT 100 int cols - BINARY prepare+execute+close")->Threads(MAX_THREAD)->UseRealTime();
BENCHMARK(BM_SELECT_100_INT_COLS_PREPARED)->Name(TYPE + " SELECT 100 int cols - BINARY execute only")->Threads(MAX_THREAD)->UseRealTime();





void do_1000_params_binary(benchmark::State& state, MYSQL* conn, MYSQL_STMT* stmt) {
  int rc;
  
  rc = mysql_stmt_execute(stmt);
  check_conn_rc(rc, conn);
}

static void BM_DO_1000_PARAMS_BINARY(benchmark::State& state) {
  MYSQL *conn = connect("");
  MYSQL_STMT *stmt = mysql_stmt_init(conn);
  
  // Build query with 1000 placeholders: "DO ?,?,?..."
  std::string query = "DO ?";
  for (int i = 1; i < 1000; i++) {
    query += ",?";
  }
  
  int rc;
  rc = mysql_stmt_prepare(stmt, query.c_str(), (unsigned long)query.size());
  check_conn_rc(rc, conn);
  
  // Prepare bind parameters - 1000 integers
  int int_data[1000];
  MYSQL_BIND my_bind[1000];
  memset(my_bind, 0, sizeof(my_bind));
  
  for (int i = 0; i < 1000; i++) {
    int_data[i] = i + 1;
    my_bind[i].buffer_type = MYSQL_TYPE_LONG;
    my_bind[i].buffer = (char *) &int_data[i];
    my_bind[i].is_null = 0;
  }
  
  rc = mysql_stmt_bind_param(stmt, my_bind);
  check_stmt_rc(rc, stmt, conn);
  
  int numOperation = 0;
  for (auto _ : state) {
    do_1000_params_binary(state, conn, stmt);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_stmt_close(stmt);
  mysql_close(conn);
}

BENCHMARK(BM_DO_1000_PARAMS_BINARY)->Name(TYPE + " DO 1000 params - BINARY execute only")->Threads(MAX_THREAD)->UseRealTime();



std::vector<std::string> chars = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "\\Z", "😎", "🌶", "🎤", "🥂" };

std::string randomString(int length) {
    std::string result = "";
    for (int i = length; i > 0; --i) {
        result += chars[rand() % (chars.size() - 1)];
    }
    return result;
}

void insert_batch_with_prepare(benchmark::State& state, MYSQL* conn) {
  MYSQL_STMT *stmt = mysql_stmt_init(conn);
  std::string query = "INSERT INTO perfTestTextBatch(t0) VALUES (?)";
  int rc;

  rc = mysql_stmt_prepare(stmt, query.c_str(), (unsigned long)query.size());
  check_conn_rc(rc, conn);

  std::string randomStringVal = randomString(100);
  char* randValue = (char *)randomStringVal.c_str();
  long unsigned randValueLen = randomStringVal.length();
  MYSQL_BIND my_bind[1];
  memset(my_bind, 0, sizeof(my_bind));

  my_bind[0].buffer_type= MYSQL_TYPE_STRING;
  my_bind[0].buffer= randValue;
  my_bind[0].length= &randValueLen;

  for (int i = 0; i < 100; i++) {
    rc = mysql_stmt_bind_param(stmt, my_bind);
    check_stmt_rc(rc, stmt, conn);

    rc = mysql_stmt_execute(stmt);
    check_conn_rc(rc, conn);
  }
  mysql_stmt_close(stmt);
}

static void BM_INSERT_BATCH_WITH_PREPARE(benchmark::State& state) {
  MYSQL *conn = connect("");
  int numOperation = 0;
  for (auto _ : state) {
    insert_batch_with_prepare(state, conn);
    numOperation++;
  }
  state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
  mysql_close(conn);
}

BENCHMARK(BM_INSERT_BATCH_WITH_PREPARE)->Name(TYPE + " insert batch looping execute")->Threads(MAX_THREAD)->UseRealTime();

#ifndef BENCHMARK_MYSQL

  void insert_bulk_batch_with_prepare(benchmark::State& state, MYSQL* conn, MYSQL_STMT *stmt) {
    int rc;
    std::string randomStringVal = randomString(100);
    char* randValue = (char *)randomStringVal.c_str();
    long randValueLen = randomStringVal.length();

    unsigned int numrows = 100;
    long unsigned value_len[100];
    char *valueptr[100];
    for (int i = 0; i < 100; i++) {
      valueptr[i]= randValue;
      value_len[i]= randValueLen;
    }

    MYSQL_BIND my_bind[1];
    memset(my_bind, 0, sizeof(my_bind));
    my_bind[0].u.indicator = 0;
    my_bind[0].buffer_type= MYSQL_TYPE_STRING;
    my_bind[0].buffer= valueptr;
    my_bind[0].length= value_len;

    rc = mysql_stmt_bind_param(stmt, my_bind);
    check_stmt_rc(rc, stmt, conn);

    mysql_stmt_attr_set(stmt, STMT_ATTR_ARRAY_SIZE, &numrows);
    rc = mysql_stmt_execute(stmt);
    check_conn_rc(rc, conn);
  }

  static void BM_INSERT_BULK_BATCH_WITH_PREPARE(benchmark::State& state) {
    MYSQL *conn = connect("");
    MYSQL_STMT *stmt = mysql_stmt_init(conn);
    std::string query = "INSERT INTO perfTestTextBatch(t0) VALUES (?)";
    int rc;

    rc = mysql_stmt_prepare(stmt, query.c_str(), (unsigned long)query.size());
    check_conn_rc(rc, conn);

    int numOperation = 0;
    for (auto _ : state) {
      insert_bulk_batch_with_prepare(state, conn, stmt);
      numOperation++;
    }
    state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
    mysql_stmt_close(stmt);
    mysql_close(conn);
  }
  BENCHMARK(BM_INSERT_BULK_BATCH_WITH_PREPARE)->Name(TYPE + " insert batch using bulk")->Threads(MAX_THREAD)->UseRealTime();

  void select_100_int_cols_with_prepare_pipeline(benchmark::State& state, MYSQL* conn) {
    MYSQL_STMT *stmt = mysql_stmt_init(conn);
    std::string query = "select * FROM test100";
    int rc;

    int int_data[100];
    unsigned long length[100];

    MYSQL_BIND my_bind[100];
    memset(my_bind, 0, sizeof(my_bind));

    for (int i = 0; i < 100; i++) {
      my_bind[i].buffer_type= MYSQL_TYPE_LONG;
      my_bind[i].buffer= (char *) &int_data[i];
      my_bind[i].length= &length[i];
    }

    rc = mariadb_stmt_execute_direct(stmt, query.c_str(), (unsigned long)query.size());
    check_conn_rc(rc, conn);

    rc = mysql_stmt_bind_result(stmt, my_bind);
    check_stmt_rc(rc, stmt, conn);

    rc = mysql_stmt_store_result(stmt);
    check_stmt_rc(rc, stmt, conn);

    while (mysql_stmt_fetch(stmt)) {
      //
    }

    mysql_stmt_close(stmt);
  }


  static void BM_SELECT_100_INT_COLS_WITH_PREPARE_PIPELINE(benchmark::State& state) {
    MYSQL *conn = connect("");
    int numOperation = 0;
    for (auto _ : state) {
      select_100_int_cols_with_prepare_pipeline(state, conn);
      numOperation++;
    }
    state.counters[OPERATION_PER_SECOND_LABEL] = benchmark::Counter(numOperation, benchmark::Counter::kIsRate);
    mysql_close(conn);
  }

  BENCHMARK(BM_SELECT_100_INT_COLS_WITH_PREPARE_PIPELINE)->Name(TYPE + " SELECT 100 int cols - BINARY pipeline prepare+execute+close")->Threads(MAX_THREAD)->UseRealTime();

#endif


BENCHMARK_MAIN();