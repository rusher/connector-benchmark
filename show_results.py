import json
import os.path
import sys
import argparse

TEXT="TEXT"
BINARY="BINARY"
BINARY_EXECUTE_ONLY="BINARY EXECUTE ONLY"
BINARY_PIPELINE="BINARY PIPELINE"
BULK="BULK"
REWRITE="REWRITE"

DO_1 = "do 1"
DO_1000 = "do 1000 parameters"
BATCH_100 = "batch 100 insert of 100 chars"
SELECT_1 = "select 1"
SELECT_1_POOL = "select 1 pool"
SELECT_100 = "Select 100 int cols"
SELECT_1000_ROWS = "select 1000 rows"

def around(x):
    if (x > 1000):
        return int(x)
    return round(x, 1)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Show benchmark results')
parser.add_argument('-l', '--language', type=str, help='Filter by language (java, c, cpp, odbc, python, go, rust, nodejs, dotnet). Multiple languages can be separated by comma: -l java,c')
parser.add_argument('--mode', type=str, choices=['sync', 'async', 'all'], default='all', help='Show sync, async, or all drivers (default: all)')
args = parser.parse_args()

# Parse languages - support comma-separated list
filter_languages = None
if args.language:
    filter_languages = [lang.strip().lower() for lang in args.language.split(',')]
filter_mode = args.mode

res = { }

# JAVA results
if(os.path.exists('./bench_results_java.json') and (filter_languages is None or 'java' in filter_languages)):
    f = open('bench_results_java.json', 'r')
    data = json.load(f)
    for i in data:
        val = around(i['primaryMetric']['score'])
        bench = ""
        type = TEXT

        if ".Do_1." in i['benchmark']:
            bench = DO_1
        elif ".Do_1000_params.text" in i['benchmark']:
            bench = DO_1000
        elif ".Do_1000_params.binary" in i['benchmark']:
            bench = DO_1000
            type = BINARY_EXECUTE_ONLY
        elif ".Insert_batch.binary" in i['benchmark']:
            bench = BATCH_100
            type = BINARY_EXECUTE_ONLY
            if (i['params']['driver'] == "mariadb"):
                type = BULK
        elif ".Insert_batch.rewrite" in i['benchmark']:
            bench = BATCH_100
            type = REWRITE
            if (i['params']['driver'] == "mariadb"):
                 type = TEXT
        elif ".Insert_batch.text" in i['benchmark']:
            bench = BATCH_100
            type = TEXT
        elif ".Select_1." in i['benchmark']:
            bench = SELECT_1
        elif ".Select_1_pool." in i['benchmark']:
            bench = SELECT_1_POOL
        elif ".Select_100_cols.text" in i['benchmark']:
            bench = SELECT_100
            type = TEXT
        elif i['benchmark'].endswith(".Select_100_cols.binary"):
            bench = SELECT_100
            type = BINARY_EXECUTE_ONLY
        elif ".Select_100_cols.binaryNoCache" in i['benchmark']:
            bench = SELECT_100
            type = BINARY_PIPELINE
            if (i['params']['driver'] == "mysql"):
                continue
        elif ".Select_100_cols.binaryNoPipeline" in i['benchmark']:
            bench = SELECT_100
            type = BINARY
        elif ".Select_1000_Rows.text" in i['benchmark']:
            bench = SELECT_1000_ROWS
            type = TEXT
        elif ".Select_1000_Rows.binary" in i['benchmark']:
            bench = SELECT_1000_ROWS
            type = BINARY_EXECUTE_ONLY
        if not bench in res:
            res[bench] = {}
        if not type in res[bench]:
            res[bench][type] = {}
        res[bench][type]['java ' + i['params']['driver']] = val
    f.close()


# GO results
if(os.path.exists('./bench_results_go.txt') and (filter_languages is None or 'go' in filter_languages)):
    f = open('bench_results_go.txt', 'r')
    lines = f.readlines()
    for line in lines:
        if line.startswith('Benchmark'):
            parts = line.split()
            val = 0
            bench = ""
            type = TEXT
            
            # Convert ns/op to operations per second (1 second = 1,000,000,000 ns)
            if len(parts) >= 4 and "ns/op" == parts[3]:
                print(parts[2])
                ns_per_op = float(parts[2])
                val = around(1000000000 / ns_per_op)
            
            if "BenchmarkSelect1Pool" == parts[0]:
                bench = SELECT_1_POOL
            elif "BenchmarkSelect1" == parts[0]:
                bench = SELECT_1
            elif "BenchmarkDo1" == parts[0]:
                bench = DO_1
            elif "BenchmarkSelect1000Rows" == parts[0]:
                bench = SELECT_1000_ROWS
            elif "BenchmarkSelect1000RowsBinary" == parts[0]:
                bench = SELECT_1000_ROWS
                type = BINARY_EXECUTE_ONLY
            elif "BenchmarkSelect100Int" == parts[0]:
                bench = SELECT_100
            elif "BenchmarkSelect100IntBinary" == parts[0]:
                bench = SELECT_100
                type = BINARY_EXECUTE_ONLY
            elif "BenchmarkDo1000Params" == parts[0]:
                bench = DO_1000
            elif "BenchmarkDo1000ParamsBinary" == parts[0]:
                bench = DO_1000
                type = BINARY_EXECUTE_ONLY

            if bench != "":
                if not bench in res:
                    res[bench] = {}
                if not type in res[bench]:
                    res[bench][type] = {}
                
                res[bench][type]['go'] = val
    f.close()

# DOTNET results
if(os.path.exists('./bench_results_dotnet.json') and (filter_languages is None or 'dotnet' in filter_languages)):
    f = open('bench_results_dotnet.json', 'r')
    data = json.load(f)['Benchmarks']
    for i in data:
        if (i['Statistics'] != None and "Mean" in i['Statistics']):
            val = around(1000000000 / i['Statistics']['Mean'])
            bench = ""
            type = TEXT
            driver = "community"
            if ("MySql.Data" in i['Parameters']):
                driver = "mysql"

            if "ExecuteDo1" == i['Method']:
                bench = DO_1
            elif "ExecuteDo1000Param" in i['Method']:
                bench = DO_1000
            elif "ExecuteDo1000PrepareParam" in i['Method']:
                bench = DO_1000
                type = BINARY_EXECUTE_ONLY
            elif "Select1000rowsText" in i['Method']:
                bench = SELECT_1000_ROWS
                type = TEXT
            elif "Select1000rowsBinary" in i['Method']:
                bench = SELECT_1000_ROWS
                type = BINARY_EXECUTE_ONLY
            elif "Select100ColText" in i['Method']:
                bench = SELECT_100
                type = TEXT
            elif "Select100ColBinary" in i['Method']:
                bench = SELECT_100
                type = BINARY_EXECUTE_ONLY
            elif ".Insert_batch.binary" in i['Method']:
                bench = BATCH_100
                type = BINARY_EXECUTE_ONLY
            elif ".Insert_batch.rewrite" in i['Method']:
                bench = BATCH_100
                type = REWRITE
            elif ".Insert_batch.text" in i['Method']:
                bench = BATCH_100
                type = TEXT
            elif "Select1" in i['Method']:
                bench = SELECT_1
            elif ".Select_100_cols.binaryNoCache" in i['Method']:
                bench = SELECT_100
                type = BINARY_PIPELINE
            elif ".Select_100_cols.binaryNoPipeline" in i['Method']:
                bench = SELECT_100
                type = BINARY

            if not bench in res:
                res[bench] = {}
            if not type in res[bench]:
                res[bench][type] = {}

            res[bench][type]['.net ' + driver] = val
    f.close()

def parseBenchResults(file, connType, language):
    if(os.path.exists(file)):
        f = open(file, 'r')
        data = json.load(f)['benchmarks']

        for i in data:
            bench = ""
            type = TEXT

            if os.getenv("TEST_DB_THREAD", default="1") + "_mean" in i['name']:
                # Calculate operations per second from real_time (in microseconds)
                if 'nb operations per second' in i:
                    val = around(float(i['nb operations per second']))
                else:
                    # Convert from microseconds to operations per second
                    val = around(1000000.0 / float(i['real_time']))
                if "DO 1/" in i['name']:
                    bench = DO_1
                elif "insert batch using bulk/" in i['name']:
                    bench = BATCH_100
                    type = BULK
                elif "insert batch client rewrite/" in i['name']:
                    bench = BATCH_100
                    type = REWRITE
                elif "insert batch looping execute/" in i['name']:
                    bench = BATCH_100
                    type = BINARY
                elif "SELECT 1/" in i['name']:
                    bench = SELECT_1
                elif "SELECT 100 int cols/" in i['name']:
                    bench = SELECT_100
                    type = TEXT
                elif "SELECT 100 int cols - BINARY execute only/" in i['name']:
                    bench = SELECT_100
                    type = BINARY_EXECUTE_ONLY
                elif "SELECT 100 int cols - BINARY pipeline prepare+execute+close/" in i['name']:
                    bench = SELECT_100
                    type = BINARY_PIPELINE
                elif "SELECT 100 int cols - BINARY prepare+execute+close/" in i['name']:
                    bench = SELECT_100
                    type = BINARY
                elif "SELECT 1000 rows (int + char(32)) - BINARY/" in i['name']:
                    bench = SELECT_1000_ROWS
                    type = BINARY_EXECUTE_ONLY
                elif "SELECT 1000 rows (int + char(32))/" in i['name']:
                    bench = SELECT_1000_ROWS
                    type = TEXT
                elif "DO 1000 params - BINARY execute only/" in i['name']:
                    bench = DO_1000
                    type = BINARY_EXECUTE_ONLY
                # ODBC benchmark names
                elif "BM_SELECT_1/" in i['name']:
                    bench = SELECT_1
                elif "BM_SELECT_1000_ROWS_TEXT/" in i['name']:
                    bench = SELECT_1000_ROWS
                    type = TEXT
                elif "BM_SELECT_1000_ROWS_BINARY/" in i['name']:
                    bench = SELECT_1000_ROWS
                    type = BINARY_EXECUTE_ONLY
                elif "BM_SELECT_100_INT_TEXT/" in i['name']:
                    bench = SELECT_100
                    type = TEXT
                elif "BM_SELECT_100_INT_BINARY/" in i['name']:
                    bench = SELECT_100
                    type = BINARY_EXECUTE_ONLY
                elif "BM_BATCH_100_INSERT_BINARY/" in i['name']:
                    bench = BATCH_100
                    type = BINARY_EXECUTE_ONLY
                else:
                    print("bench not recognized : " + i['name'])

                if bench != "":
                    if not bench in res:
                        res[bench] = {}
                    if not type in res[bench]:
                        res[bench][type] = {}
                    res[bench][type][language + ' ' + connType] = val

        f.close()

# C mariadb results
if filter_languages is None or 'c' in filter_languages:
    parseBenchResults("./bench_results_c_mysql.json", "mysql", "c")
    parseBenchResults("./bench_results_c_mariadb.json", "mariadb", "c")

# C++ mariadb results
if filter_languages is None or any(lang in filter_languages for lang in ['c++', 'cpp']):
    parseBenchResults("./bench_results_cpp_mysql.json", "mysql", "c++")
    parseBenchResults("./bench_results_cpp_mariadb.json", "mariadb", "c++")

# ODBC results
if filter_languages is None or 'odbc' in filter_languages:
    parseBenchResults("./bench_results_odbc_mariadb.json", "mariadb", "odbc")
    parseBenchResults("./bench_results_odbc_mysql.json", "mysql", "odbc")


if(os.path.exists('./bench_results_nodejs.json') and (filter_languages is None or any(lang in filter_languages for lang in ['nodejs', 'node']))):
    f = open('bench_results_nodejs.json', 'r')
    data = json.load(f)

    for benchType in data:
        for curRes in data[benchType]:
            val = around(curRes['iteration'])
            bench = ""
            type = TEXT

            if benchType == "do 1":
                bench = DO_1
            elif benchType == "do 1000 parameter":
                bench = DO_1000
            elif benchType == "do 1000 parameter - BINARY":
                bench = DO_1000
                type = BINARY_EXECUTE_ONLY
            elif benchType.startswith("100 * insert 100 characters using batch method"):
                bench = BATCH_100
                type = TEXT
                if (curRes['name'] == "mariadb"):
                    type = BULK
            elif benchType == 'select 1':
                bench = SELECT_1
            elif benchType == 'SELECT 1 - pool (16 connections, 100 concurrent)':
                bench = SELECT_1_POOL
            elif benchType == 'select 100 int/varchar(32)':
                bench = SELECT_100
                type = TEXT
            elif benchType == 'select 100 int/varchar(32) - BINARY':
                bench = SELECT_100
                type = BINARY_EXECUTE_ONLY
            elif benchType == "select 1000 rows":
                bench = SELECT_1000_ROWS
                type = TEXT
            elif benchType == "select 1000 rows - BINARY":
                bench = SELECT_1000_ROWS
                type = BINARY_EXECUTE_ONLY
            else:
                print("bench not recognized : " + benchType)
            if bench != '':
                if not bench in res:
                    res[bench] = {}
                if not type in res[bench]:
                    res[bench][type] = {}
                res[bench][type]['node ' + curRes['name']] = val
    f.close()


# RUST results
def parseRustRes(path, type, bench, name):
    if(os.path.exists(f"./scripts/rust/target/criterion/bench/{path}/base/estimates.json")):
        f = open(f"scripts/rust/target/criterion/bench/{path}/base/estimates.json", 'r')
        data = json.load(f)
        val = around(1000000000 / data['mean']['point_estimate'])
        if not bench in res:
            res[bench] = {}
        if not type in res[bench]:
            res[bench][type] = {}
        res[bench][type][name] = val
        f.close()

if filter_languages is None or 'rust' in filter_languages:
    parseRustRes("do 1", TEXT, DO_1, 'rust mysql')
    parseRustRes("do 1000 param", BINARY_EXECUTE_ONLY, DO_1000, 'rust mysql')
    parseRustRes("select 1", TEXT, SELECT_1, 'rust mysql')
    parseRustRes("select 1000 rows", TEXT, SELECT_1000_ROWS, 'rust mysql')
    parseRustRes("select 1000 rows binary", BINARY_EXECUTE_ONLY, SELECT_1000_ROWS, 'rust mysql')
    parseRustRes("select 100 int columns", TEXT, SELECT_100, 'rust mysql')

    parseRustRes("sqlx do 1", TEXT, DO_1, 'rust sqlx')
    parseRustRes("sqlx do 1000 param", BINARY_EXECUTE_ONLY, DO_1000, 'rust sqlx')
    parseRustRes("sqlx select 1", TEXT, SELECT_1, 'rust sqlx')
    parseRustRes("sqlx select 1000 rows", TEXT, SELECT_1000_ROWS, 'rust sqlx')
    parseRustRes("sqlx select 1000 rows binary", BINARY_EXECUTE_ONLY, SELECT_1000_ROWS, 'rust sqlx')
    parseRustRes("sqlx select 100 int columns", TEXT, SELECT_100, 'rust sqlx')

    parseRustRes("mysql_async do 1", TEXT, DO_1, 'rust mysql_async')
    parseRustRes("mysql_async do 1000 param", BINARY_EXECUTE_ONLY, DO_1000, 'rust mysql_async')
    parseRustRes("mysql_async select 1", TEXT, SELECT_1, 'rust mysql_async')
    parseRustRes("mysql_async select 1000 rows", TEXT, SELECT_1000_ROWS, 'rust mysql_async')
    parseRustRes("mysql_async select 1000 rows binary", BINARY_EXECUTE_ONLY, SELECT_1000_ROWS, 'rust mysql_async')
    parseRustRes("mysql_async select 100 int columns", TEXT, SELECT_100, 'rust mysql_async')


def parsePythonBenchResults(file, connType):
    if(os.path.exists(file)):
        f = open(file, 'r')
        try:
            data = json.load(f)['benchmarks']
        except (json.JSONDecodeError, KeyError):
            print(f"Warning: Could not parse {file}, skipping")
            f.close()
            return

        for i in data:
            bench = ""
            type = TEXT
            
            # New pytest-benchmark format: mean time in seconds, convert to ops/sec
            mean_time = i['stats']['mean']
            val = around(1.0 / mean_time)
            
            # Extract benchmark name from test name (e.g., "test_bench_do_1[mariadb]")
            test_name = i['name']
            
            if "test_bench_do_1[" in test_name or "test_do_1[" in test_name:
                bench = DO_1
            elif "test_do_1_async[" in test_name:
                bench = DO_1
            elif "test_bench_insert_batch[" in test_name or "test_insert_batch[" in test_name:
                bench = BATCH_100
                # Check if it's bulk insert based on driver
                if connType in ["mariadb", "mariadb_c"]:
                    type = BULK
                else:
                    type = REWRITE
            elif "test_insert_batch_async[" in test_name:
                bench = BATCH_100
                # Check if it's bulk insert based on driver
                if connType in ["async-mariadb"]:
                    type = BULK
                else:
                    type = REWRITE
            elif "test_bench_select_1[" in test_name or "test_select_1[" in test_name:
                bench = SELECT_1
            elif "test_select_1_async[" in test_name:
                bench = SELECT_1
            elif "test_select_1_pool[" in test_name:
                bench = SELECT_1_POOL
            elif "test_select_100_cols_text[" in test_name:
                bench = SELECT_100
                type = TEXT
            elif "test_select_100_cols_async[" in test_name:
                bench = SELECT_100
                type = TEXT
            elif "test_select_100_cols_binary[" in test_name:
                bench = SELECT_100
                type = BINARY_EXECUTE_ONLY
            elif "test_bench_select_100_cols[" in test_name or "test_select_100_cols[" in test_name:
                bench = SELECT_100
                if "execute" in test_name.lower() or "binary" in test_name.lower():
                    type = BINARY_EXECUTE_ONLY
                else:
                    type = TEXT
            elif "test_select_1000_rows_text[" in test_name:
                bench = SELECT_1000_ROWS
                type = TEXT
            elif "test_select_1000_rows_async[" in test_name:
                bench = SELECT_1000_ROWS
                type = TEXT
            elif "test_select_1000_rows_binary[" in test_name:
                bench = SELECT_1000_ROWS
                type = BINARY_EXECUTE_ONLY
            elif "test_bench_select_1000_rows[" in test_name or "test_select_1000_rows[" in test_name:
                bench = SELECT_1000_ROWS
                if "binary" in test_name.lower():
                    type = BINARY_EXECUTE_ONLY
                else:
                    type = TEXT
            elif "test_do_1000_params_text[" in test_name:
                bench = DO_1000
                type = TEXT
            elif "test_do_1000_params_async[" in test_name:
                bench = DO_1000
                type = TEXT
            elif "test_do_1000_params_binary[" in test_name:
                bench = DO_1000
                type = BINARY_EXECUTE_ONLY
            else:
                print("bench not recognized : " + test_name)

            if bench != "":
                if not bench in res:
                    res[bench] = {}
                if not type in res[bench]:
                    res[bench][type] = {}
                res[bench][type]['python ' + connType] = val

        f.close()

if filter_languages is None or 'python' in filter_languages:
    parsePythonBenchResults("bench_results_python_mariadb_results.json", "mariadb")
    parsePythonBenchResults("bench_results_python_mariadb_c_results.json", "mariadb_c")
    parsePythonBenchResults("bench_results_python_async-mariadb_results.json", "async-mariadb")
    parsePythonBenchResults("bench_results_python_pymysql_results.json", "pymysql")
    parsePythonBenchResults("bench_results_python_mysql_connector_results.json", "mysql_connector")
    parsePythonBenchResults("bench_results_python_mysql_connector_async_results.json", "mysql_connector_async")
    parsePythonBenchResults("bench_results_python_asyncmy_results.json", "asyncmy")



# Define async drivers
ASYNC_DRIVERS = [
    'async-mariadb', 'mysql_connector_async', 'asyncmy',  # Python async only
    'sqlx', 'mysql_async',  # Rust async
    'mysql', 'community',  # .NET (both MySql.Data and MySqlConnector are async)
    'mysql2', 'mariadb'  # Node.js (both mysql2 and mariadb are async)
]

# Sync drivers (for reference):
# - Java: mysql, mariadb (sync)
# - C: mysql, mariadb (sync)
# - Go: (sync)
# - Rust: mysql (sync version)
# - Python: mariadb, mariadb_c, pymysql, mysql_connector (sync)

def is_async_driver(connType):
    """Check if a connector type is an async driver."""
    # Check for Node.js drivers (all async)
    if connType.startswith('node '):
        return True
    
    # Check for .NET drivers (all async)
    if connType.startswith('.net '):
        return True
    
    # Check for Rust async drivers
    if 'sqlx' in connType or 'mysql_async' in connType:
        return True
    
    # Check for Python async drivers
    parts = connType.split()
    driver = parts[1] if len(parts) > 1 else ""
    if driver in ['async-mariadb', 'mysql_connector_async', 'asyncmy']:
        return True
    
    return False

# Separate sync and async connector types
syncConnectorTypes = ()
asyncConnectorTypes = ()

for bench in res:
    for type in res[bench]:
        for connType in res[bench][type]:
            if is_async_driver(connType):
                if not connType in asyncConnectorTypes:
                    asyncConnectorTypes = asyncConnectorTypes + (connType,)
            else:
                if not connType in syncConnectorTypes:
                    syncConnectorTypes = syncConnectorTypes + (connType,)

# Select which connector types to display based on filter_mode
if filter_mode == 'sync':
    connectorTypes = syncConnectorTypes
elif filter_mode == 'async':
    connectorTypes = asyncConnectorTypes
else:  # 'all'
    connectorTypes = syncConnectorTypes + asyncConnectorTypes


def print_results_table(connectorTypes, title=None):
    """Print a results table for the given connector types."""
    if not connectorTypes:
        return
        
    if title:
        print("")
        print(title)
        print("")
    
    # Top border
    header1 = "{:53} |".format("")
    for connectorType in connectorTypes:
        header1 = header1 + "{:14}|".format("".ljust(14,"-"))
    print(header1)

    # First line of connector names (language)
    header_line1 = "{:53} |".format("")
    for connectorType in connectorTypes:
        parts = connectorType.split()
        language = parts[0] if len(parts) > 0 else ""
        if len(language) > 13:
            language = language[0:12] + "."
        header_line1 = header_line1 + " {:13}|".format(language)
    print(header_line1)

    # Second line of connector names (driver)
    header_line2 = "{:53} |".format("")
    for connectorType in connectorTypes:
        parts = connectorType.split()
        driver = parts[1] if len(parts) > 1 else ""
        if len(driver) > 13:
            driver = driver[0:12] + "."
        header_line2 = header_line2 + " {:13}|".format(driver)
    print(header_line2)

    # Bottom border
    header1 = "{:54}|".format("".ljust(54,"-"))
    for connectorType in connectorTypes:
        header1 = header1 + "{:14}|".format("".ljust(14,"-"))
    print(header1)

    # Print detailed results
    for bench in res:
        for type in res[bench]:
            # Use fastest C connector as reference (100%), or max if C not present
            refVal = 0
            # Find the fastest between C mysql and C mariadb
            for c_connector in ['c mysql', 'c mariadb']:
                if c_connector in res[bench][type]:
                    if res[bench][type][c_connector] > refVal:
                        refVal = res[bench][type][c_connector]
            
            # If no C connector, fall back to max value
            if refVal == 0:
                for connectorType in connectorTypes:
                    if connectorType in res[bench][type]:
                        if res[bench][type][connectorType] > refVal:
                            refVal = res[bench][type][connectorType]
            
            if refVal == 0:  # Skip if no data for these connectors
                continue
                
            line = "{:30} - {:20} |".format(bench, type)
            for connectorType in connectorTypes:
                if (not connectorType in res[bench][type]):
                    line = line + "{:6.0} | {:4.0} |".format("", "")
                else:
                    val = res[bench][type][connectorType]
                    line = line + "{:6.0f} | {:4.0%} |".format(val, val / refVal)
            print(line)
    print(header1)

    # Aggregate results
    result2 = {}
    for bench in res:
        for type in res[bench]:
            for connectorType in connectorTypes:
                if (connectorType in res[bench][type]):
                    val = res[bench][type][connectorType]
                    if not bench in result2:
                        result2[bench] = {}
                    if not connectorType in result2[bench]:
                        result2[bench][connectorType] = val
                    else:
                        currVal = result2[bench][connectorType]
                        if (currVal < val):
                            result2[bench][connectorType] = val

    print("")
    print("")
    print("agreggate results:")
    print("")

    # Top border
    header1 = "{:30} |".format("")
    for connectorType in connectorTypes:
        header1 = header1 + "{:14}|".format("".ljust(14,"-"))
    print(header1)

    # First line of connector names (language)
    header_line1 = "{:30} |".format("")
    for connectorType in connectorTypes:
        parts = connectorType.split()
        language = parts[0] if len(parts) > 0 else ""
        if len(language) > 13:
            language = language[0:12] + "."
        header_line1 = header_line1 + " {:13}|".format(language)
    print(header_line1)

    # Second line of connector names (driver)
    header_line2 = "{:30} |".format("")
    for connectorType in connectorTypes:
        parts = connectorType.split()
        driver = parts[1] if len(parts) > 1 else ""
        if len(driver) > 13:
            driver = driver[0:12] + "."
        header_line2 = header_line2 + " {:13}|".format(driver)
    print(header_line2)

    # Bottom border
    header1 = "{:31}|".format("".ljust(31,"-"))
    for connectorType in connectorTypes:
        header1 = header1 + "{:14}|".format("".ljust(14,"-"))
    print(header1)

    # Print aggregate results
    for bench in result2:
        # Use fastest C connector as reference (100%), or max if C not present
        refVal = 0
        # Find the fastest between C mysql and C mariadb
        for c_connector in ['c mysql', 'c mariadb']:
            if c_connector in result2[bench]:
                if result2[bench][c_connector] > refVal:
                    refVal = result2[bench][c_connector]
        
        # If no C connector, fall back to max value
        if refVal == 0:
            for connectorType in result2[bench]:
                if (result2[bench][connectorType] > refVal):
                    refVal = result2[bench][connectorType]
        
        line = "{:30} |".format(bench)
        for connectorType in connectorTypes:
            if (not connectorType in result2[bench]):
                line = line + "{:6.0} | {:4.0} |".format("", "")
            else:
                val = result2[bench][connectorType]
                line = line + "{:6.0f} | {:4.0%} |".format(val, val / refVal)
        print(line)
    print(header1)


# Print tables based on filter_mode
if filter_mode == 'all':
    # Print separate tables for sync and async
    if syncConnectorTypes:
        print_results_table(syncConnectorTypes, "=== SYNC DRIVERS ===")
    if asyncConnectorTypes:
        print_results_table(asyncConnectorTypes, "=== ASYNC DRIVERS ===")
else:
    # Print single table for filtered mode
    print_results_table(connectorTypes)

