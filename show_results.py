import json
import os.path
from math import log10, floor

TEXT="TEXT"
BINARY="BINARY"
BINARY_CACHE="BINARY CLIENT CACHE"
BINARY_PIPELINE="BINARY PIPELINE"
BULK="BULK"
REWRITE="REWRITE"

DO_1 = "do 1"
DO_1000 = "do 1000 parameters"
BATCH_100 = "batch 100 insert of 100 chars"
SELECT_1 = "select 1"
SELECT_100 = "Select 100 int cols"
SELECT_1000_ROWS = "SELECT 1000 rows"

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
        elif ".Do_1000_params." in i['benchmark']:
            bench = DO_1000
        elif ".Insert_batch.binary" in i['benchmark']:
            bench = BATCH_100
            type = BINARY_CACHE
            if (i['params']['driver'] == "mariadb"):
                type = BULK
        elif ".Insert_batch.rewrite" in i['benchmark']:
            bench = BATCH_100
            type = REWRITE
            if (i['params']['driver'] == "mariadb"):
                 type = TEXT
        elif ".Select_1." in i['benchmark']:
            bench = SELECT_1
        elif ".Select_100_cols.text" in i['benchmark']:
            bench = SELECT_100
            type = TEXT
        elif i['benchmark'].endswith(".Select_100_cols.binary"):
            bench = SELECT_100
            type = BINARY_CACHE
        elif ".Select_100_cols.binaryNoCache" in i['benchmark']:
            bench = SELECT_100
            type = BINARY_PIPELINE
        elif ".Select_100_cols.binaryNoPipeline" in i['benchmark']:
            bench = SELECT_100
            type = BINARY
        elif ".Select_1000_Rows.text" in i['benchmark']:
            bench = SELECT_1000_ROWS
            type = TEXT
        elif ".Select_1000_Rows.binary" in i['benchmark']:
            bench = SELECT_1000_ROWS
            type = BINARY_CACHE
        if not bench in res:
            res[bench] = {}
        if not type in res[bench]:
            res[bench][type] = {}
        res[bench][type]['java ' + i['params']['driver']] = val
    f.close()


def parseBenchResults(file, connType, language):
    if(os.path.exists(file)):
        f = open(file, 'r')
        data = json.load(f)['benchmarks']

        for i in data:
            bench = ""
            type = TEXT

            if "1_mean" in i['name']:
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
                    type = BINARY_CACHE
                elif "SELECT 100 int cols - BINARY pipeline prepare+execute+close/" in i['name']:
                    bench = SELECT_100
                    type = BINARY_PIPELINE
                elif "SELECT 100 int cols - BINARY prepare+execute+close/" in i['name']:
                    bench = SELECT_100
                    type = BINARY
                elif "SELECT 1000 rows (int + char(32))/" in i['name']:
                    bench = SELECT_1000_ROWS
                    type = TEXT
                elif "DO 1000 params/" in i['name']:
                    if not (language == "c"):
                        bench = DO_1000
                        if (connType == "mysql"):
                            type = BINARY
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
                type = BINARY_CACHE
            elif benchType == "select 1000 rows":
                bench = SELECT_1000_ROWS
                type = TEXT
            else:
                print("bench not recognized : " + benchType)
            if bench != '':
                if not bench in res:
                    res[bench] = {}
                if not type in res[bench]:
                    res[bench][type] = {}
                res[bench][type]['node ' + curRes['name']] = val
    f.close()




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
    header = header + " {:12} |".format(connectorType)
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
#print(res)
