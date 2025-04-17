import json
import os.path

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
SELECT_100 = "Select 100 int cols"
SELECT_1000_ROWS = "select 1000 rows"

def around(x):
    if (x > 1000):
        return int(x)
    return round(x, 1)

res = { }

# JAVA results
if(os.path.exists('./bench_results_java.json')):
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
if(os.path.exists('./bench_results_go.txt')):
    f = open('bench_results_go.txt', 'r')
    lines = f.readlines()
    for line in lines:
        print(line)
        if line.startswith('Benchmark'):
            parts = line.split()
            print(parts)
            val = 0
            bench = ""
            type = TEXT
            
            # Convert ns/op to operations per second (1 second = 1,000,000,000 ns)
            if len(parts) >= 4 and "ns/op" == parts[3]:
                print(parts[2])
                ns_per_op = float(parts[2])
                val = around(1000000000 / ns_per_op)
            
            if "BenchmarkSelect1" == parts[0]:
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
if(os.path.exists('./bench_results_dotnet.json')):
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
            elif "Select1000rowsText" == i['Method']:
                bench = SELECT_1000_ROWS
                type = TEXT
            elif "Select1000rowsBinary" == i['Method']:
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
                val = around(float(i['nb operations per second']))
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
                elif "SELECT 1000 rows (int + char(32))/" in i['name']:
                    bench = SELECT_1000_ROWS
                    type = TEXT
                # elif "DO 1000 params/" in i['name']:
                #     # if not (language == "c"):
                #     bench = DO_1000
                #     type = TEXT
                #     # if (connType == "mysql"):
                #     #     type = BINARY
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
parseBenchResults("./bench_results_c_mysql.json", "mysql", "c")
parseBenchResults("./bench_results_c_mariadb.json", "mariadb", "c")

# C++ mariadb results
parseBenchResults("./bench_results_cpp_mysql.json", "mysql", "c++")
parseBenchResults("./bench_results_cpp_mariadb.json", "mariadb", "c++")



if(os.path.exists('./bench_results_nodejs.json')):
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
        data = json.load(f)['benchmarks']

        for i in data:
            bench = ""
            type = TEXT
            val = 0
            for tmpVal in i['runs'][1]['values']:
                val += float(tmpVal)
            length = len(i['runs'][1]['values'])
            val = around(1 / (val / length))
            if "DO 1" == i['metadata']['name']:
                bench = DO_1
            elif "BULK Insert" == i['metadata']['name']:
                bench = BATCH_100
                type = BULK
                if (connType == "mysql"):
                    type = BINARY
            elif "select 1" == i['metadata']['name']:
                bench = SELECT_1
            elif "select_100_cols" == i['metadata']['name']:
                bench = SELECT_100
                type = TEXT
            elif "select_1000_rows" == i['metadata']['name']:
                bench = SELECT_1000_ROWS
                type = TEXT
            elif "select 1000 rows - BINARY" == i['metadata']['name']:
                bench = SELECT_1000_ROWS
                type = BINARY_EXECUTE_ONLY
            elif "select_100_cols_execute" == i['metadata']['name']:
                bench = SELECT_100
                type = BINARY_EXECUTE_ONLY
            elif "DO 1000 params" == i['metadata']['name']:
                bench = DO_1000
                type = BINARY_EXECUTE_ONLY
            else:
                print("bench not recognized : " + i['metadata']['name'])

            if bench != "":
                if not bench in res:
                    res[bench] = {}
                if not type in res[bench]:
                    res[bench][type] = {}
                res[bench][type]['python ' + connType] = val

        f.close()

parsePythonBenchResults("bench_results_python_mariadb_results.json", "mariadb")
parsePythonBenchResults("bench_results_python_mysql_results.json", "mysql")



connectorTypes = ()

for bench in res:
    for type in res[bench]:
        for connType in res[bench][type]:
            if not connType in connectorTypes:
                connectorTypes = connectorTypes + (connType,)


header1 = "{:53} |".format("")
for connectorType in connectorTypes:
    header1 = header1 + "{:14}|".format("".ljust(14,"-"))
print(header1)
header = "{:53} |".format("")
for connectorType in connectorTypes:
    v = connectorType
    if (len(v) > 13):
        v = v[0:12] + "."
    header = header + " {:13}|".format(v)
print(header)

header1 = "{:54}|".format("".ljust(54,"-"))
for connectorType in connectorTypes:
    header1 = header1 + "{:14}|".format("".ljust(14,"-"))
print(header1)


form = "{:30} - {:20} |"

for bench in res:
    for type in res[bench]:
        maxVal = 0
        for connectorType in res[bench][type]:
            if (res[bench][type][connectorType] > maxVal):
                maxVal = res[bench][type][connectorType]
        line = "{:30} - {:20} |".format(bench, type)
        for connectorType in connectorTypes:
            if (not connectorType in res[bench][type]):
                line = line + "{:6.0} | {:4.0} |".format("", "")
            else:
                val = res[bench][type][connectorType]
                line = line + "{:6.0f} | {:4.0%} |".format(val, val / maxVal)
        print(line)
print(header1)

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

header1 = "{:30} |".format("")
for connectorType in connectorTypes:
    header1 = header1 + "{:14}|".format("".ljust(14,"-"))
print(header1)
header = "{:30} |".format("")
for connectorType in connectorTypes:
    v = connectorType
    if (len(v) > 13):
        v = v[0:12] + "."
    header = header + " {:13}|".format(v)
print(header)

header1 = "{:31}|".format("".ljust(31,"-"))
for connectorType in connectorTypes:
    header1 = header1 + "{:14}|".format("".ljust(14,"-"))
print(header1)


form = "{:30} |"

for bench in result2:
    maxVal = 0
    for connectorType in result2[bench]:
        if (result2[bench][connectorType] > maxVal):
            maxVal = result2[bench][connectorType]
    line = "{:30} |".format(bench)
    for connectorType in connectorTypes:
        if (not connectorType in result2[bench]):
            line = line + "{:6.0} | {:4.0} |".format("", "")
        else:
            val = result2[bench][connectorType]
            line = line + "{:6.0f} | {:4.0%} |".format(val, val / maxVal)
    print(line)
print(header1)

