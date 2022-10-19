# Benchmark MariaDB/MySQL connector

available languages : 
* c
* c++
* java


How to run : 
```script
# install dependencies
sudo ./bench.sh -i

# run benchmark, results will be in bench_results_*.json files
sudo ./bench.sh

# view results
python show_results.py 
```

or for a specific language
```script
# install dependencies
sudo ./bench.sh -i -l c

# run benchmark
sudo ./bench.sh -l c

# view results
python show_results.py 
```


possible options :
* l: language. java, c, c++. nothing means all.
* t: type mariadb/mysql. nothing means all.
* i: installation (no parameters). It will build/install requirement for designated language(s)
* p: server port. default 3306 if not set
* h:  server host. default means '127.0.0.1'
* d: database. default "bench"
* p: password.
