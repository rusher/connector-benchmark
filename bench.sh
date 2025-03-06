#!/bin/bash

set -e -x -o pipefail

############################################################################
############################# installation #################################
############################################################################

# install java and maven
installation_java () {
  apt update
  apt install -y openjdk-17-jdk
  apt install -y maven
  java -version
  mvn -version
}

installation_rust () {
  apt update
  sudo apt install cargo
  # curl https://sh.rustup.rs -sSf | sh
}

installation_c () {
  apt update
  apt install -y software-properties-common build-essential cmake libssl-dev
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-c/" ]]
  then
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-c.git
  fi

  mkdir -p $PROJ_PATH/repo/build-c
  cd $PROJ_PATH/repo/build-c
  cmake ../mariadb-connector-c -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
  cmake --build . --config Release  --target install
  echo $LD_LIBRARY_PATH
  apt install -y libmysqlclient-dev
}

installation_cpp () {
  apt update
  apt install -y software-properties-common build-essential cmake libssl-dev
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-cpp/" ]]
  then
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-cpp.git
  fi
  mkdir -p $PROJ_PATH/repo/build-cpp
  cd $PROJ_PATH/repo/build-cpp
  cmake ../mariadb-connector-cpp -DCONC_WITH_MSI=OFF -DCONC_WITH_UNIT_TESTS=OFF -DCMAKE_BUILD_TYPE=Release -DWITH_SSL=OPENSSL
  sudo cmake --build . --config Release  --target install
  sudo make install
  sudo install /usr/local/lib/mariadb/libmariadbcpp.so /usr/lib
  sudo install -d /usr/lib/mariadb
  sudo install -d /usr/lib/mariadb/plugin
  sudo ldconfig -n /usr/local/lib/mariadb || true
  sudo ldconfig -l -v /usr/lib/libmariadbcpp.so || true

  sudo apt-get -y install libmysqlcppconn-dev
}

installation_python () {
  apt update
  apt install -y software-properties-common build-essential cmake libssl-dev python-is-python3
  python --version
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-python/" ]]
  then
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-python.git
  fi
  cd $PROJ_PATH/repo/mariadb-connector-python
  pip install --upgrade pip
  pip install packaging
  python setup.py build
  python setup.py install
  cd $PROJ_PATH/scripts/python
  pip install mysql-connector-python pyperf
}

installation_benchmark () {
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  # Check out the library.
  if [[ -e "${PROJ_PATH}/repo/benchmark/" ]]
  then
    git pull
  else
    git clone https://github.com/google/benchmark.git
  fi

  # Go to the library root directory
  cd benchmark
  # Make a build directory to place the build output.
  cmake -E make_directory "build"
  # Generate build system files with cmake, and download any dependencies.
  cmake -E chdir "build" cmake -DBENCHMARK_DOWNLOAD_DEPENDENCIES=on -DCMAKE_BUILD_TYPE=Release ../
  # or, starting with CMake 3.13, use a simpler form:
  # cmake -DCMAKE_BUILD_TYPE=Release -S . -B "build"
  # Build the library.
  cmake --build "build" --config Release --target install
}

installation_nodejs () {
  curl -sL https://deb.nodesource.com/setup_18.x -o /tmp/nodesource_setup.sh
  sudo bash /tmp/nodesource_setup.sh
  apt update
  sudo apt -y install nodejs
  node -v
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-nodejs/" ]]
  then
    cd mariadb-connector-nodejs
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-nodejs.git
    cd mariadb-connector-nodejs
    git checkout develop
  fi
  npm install
  cd $PROJ_PATH/scripts/node
  npm install
}

installation_setup () {
  apt update
  apt install -y software-properties-common build-essential  python-is-python3
  python --version
  cd $PROJ_PATH/scripts/setup
  python -m venv venv
  source venv/bin/activate
  pip install packaging
  pip install mysql-connector-python
}


############################################################################
############################# launcher #####################################
############################################################################

launch_java_bench () {
  cd $PROJ_PATH/scripts/java
  mvn clean package
  java -Duser.country=US -Duser.language=en -jar target/benchmarks.jar -rf json -rff $PROJ_PATH/bench_results_java.json
}

launch_rust_bench () {
  cd $PROJ_PATH/scripts/rust
  cargo --version
  export PATH="$HOME/.cargo/bin:$PATH"
  cargo --version
#  cargo bench -q --message-format=json
  cargo bench -q
}

launch_python_bench () {
  cd $PROJ_PATH/scripts/python
  if [ -n "$TYPE" ] ; then
    case $TYPE in
      mariadb)
        rm -f $PROJ_PATH/bench_results_python_mariadb_results.json
        export TEST_MODULE=mariadb
        python bench.py -o $PROJ_PATH/bench_results_python_mariadb_results.json --inherit-environ=TEST_MODULE,TEST_DB_USER,TEST_DB_HOST,TEST_DB_DATABASE,TEST_DB_PORT,TEST_DB_PASSWORD --copy-env
        ;;
      mysql)
        rm -f $PROJ_PATH/bench_results_python_mysql_results.json
        export TEST_MODULE=mysql.connector
        python bench.py -o $PROJ_PATH/bench_results_python_mysql_results.json --inherit-environ=TEST_MODULE,TEST_DB_USER,TEST_DB_HOST,TEST_DB_DATABASE,TEST_DB_PORT,TEST_DB_PASSWORD --copy-env
        ;;
      *)
        echo "wrong value for type (parameter t) must be either mariadb or mysql. Provided:$TYPE"
        exit 30
        ;;
    esac
  else
    rm -f $PROJ_PATH/bench_results_python_mariadb_results.json
    export TEST_MODULE=mariadb
    python bench.py -o $PROJ_PATH/bench_results_python_mariadb_results.json --inherit-environ=TEST_MODULE,TEST_DB_USER,TEST_DB_HOST,TEST_DB_DATABASE,TEST_DB_PORT,TEST_DB_PASSWORD --copy-env
    rm -f $PROJ_PATH/bench_results_python_mysql_results.json
    export TEST_MODULE=mysql.connector
    python bench.py -o $PROJ_PATH/bench_results_python_mysql_results.json --inherit-environ=TEST_MODULE,TEST_DB_USER,TEST_DB_HOST,TEST_DB_DATABASE,TEST_DB_PORT,TEST_DB_PASSWORD --copy-env
  fi
}

launch_c_bench () {
  cd $PROJ_PATH/scripts/c
  if [ -n "$TYPE" ] ; then
    case $TYPE in
      mariadb)
        g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -I/usr/local/include/mariadb -I/usr/local/include/mariadb/mysql -L/usr/local/lib/mariadb/ -lmariadb -lbenchmark -lpthread -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mariadb_results.json
        ;;
      mysql)
        g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DBENCHMARK_MYSQL -lmysqlclient -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mysql.json
        ;;
      *)
        echo "wrong value for type (parameter t) must be either mariadb or mysql. Provided:$TYPE"
        exit 30
        ;;
    esac
  else
    g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -I/usr/local/include/mariadb -I/usr/local/include/mariadb/mysql -L/usr/local/lib/mariadb/ -lmariadb -lbenchmark -lpthread -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mariadb.json
    g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DBENCHMARK_MYSQL -lmysqlclient -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mysql.json
  fi

}

launch_cpp_bench () {
  cd $PROJ_PATH/scripts/cpp
  if [ -n "$TYPE" ] ; then
    case $TYPE in
      mariadb)
        g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -L/usr/local/lib/mariadb/ -lbenchmark -lpthread -lmariadbcpp -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mariadb.json
        ;;
      mysql)
        g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DMYSQL -lmysqlcppconn -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mysql.json
        ;;
      *)
        echo "wrong value for type (parameter t) must be either mariadb or mysql. Provided:$TYPE"
        exit 30
        ;;
    esac
  else
    g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -L/usr/local/lib/mariadb/ -lbenchmark -lpthread -lmariadbcpp -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mariadb.json
    g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DMYSQL -lmysqlcppconn -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mysql.json
  fi
}


launch_nodejs_bench () {
  cd $PROJ_PATH/scripts/node
  npm run benchmark
}

execute_setup () {
  source venv/bin/activate
  cd $PROJ_PATH/scripts/setup
  python ./setup.py
}


############################################################################
##############################" executor ##################################
############################################################################

export PROJ_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "parsing parameters"

INSTALLATION=false
export TEST_USE_SSL=false
export TEST_DB_HOST=127.0.0.1
export TEST_DB_PORT=3306
export TEST_DB_USER=root
export TEST_DB_DATABASE=bench
export TEST_OTHER=
export TEST_DB_THREAD=1

while getopts ":l:t:isp:h:d:u:w:" flag; do
  case "${flag}" in
    l) export LANGUAGE=${OPTARG};;
    t) export TYPE=${OPTARG};;
    i) INSTALLATION=true;;
    s) export TEST_USE_SSL=true;;
    p) export TEST_DB_PORT=${OPTARG};;
    h) export TEST_DB_HOST=${OPTARG};;
    d) export TEST_DB_DATABASE=${OPTARG};;
    u) export TEST_DB_USER=${OPTARG};;
    w) export TEST_DB_PASSWORD=${OPTARG};;
  esac
done

echo "parameters:"
echo "TYPE: ${TYPE}"
echo "INSTALLATION: ${INSTALLATION}"
echo "LANGUAGE: ${LANGUAGE}"
echo "TEST_DB_HOST: ${TEST_DB_HOST}"
echo "TEST_DB_PORT: ${TEST_DB_PORT}"
echo "TEST_DB_USER: ${TEST_DB_USER}"
echo "TEST_DB_DATABASE: ${TEST_DB_DATABASE}"
echo "TEST_DB_PASSWORD: ${TEST_DB_PASSWORD}"
echo "TEST_USE_SSL: ${TEST_USE_SSL}"


if [[ $INSTALLATION == true ]]; then
  installation_setup
  source venv/bin/activate
  case $LANGUAGE in
    java)
      installation_java
      ;;
    python)
      installation_setup
      installation_c
      installation_python
      ;;
    c)
      installation_setup
      installation_c
      installation_benchmark
      ;;
    cpp)
      installation_setup
      installation_c
      installation_cpp
      installation_benchmark
      ;;
    node)
      installation_setup
      installation_nodejs
      ;;
    rust)
      installation_rust
      ;;
    *)
      installation_setup
      installation_c
      installation_cpp
      installation_python
      installation_benchmark
      installation_java
      installation_nodejs
      installation_rust
      ;;
  esac
else
  source venv/bin/activate
  execute_setup

  if [[ $LD_LIBRARY_PATH != *":/usr/local/lib"* ]]; then
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/mariadb
  fi
  case $LANGUAGE in
    java)
      launch_java_bench
      ;;
    python)
      launch_python_bench
      ;;
    c)
      launch_c_bench
      ;;
    cpp)
      launch_cpp_bench
      ;;
    node)
      launch_nodejs_bench
      ;;
    rust)
      launch_rust_bench
      ;;
    *)
      launch_java_bench
      launch_c_bench
      launch_cpp_bench
      launch_nodejs_bench
      launch_rust_bench
      ;;
  esac
  cd $PROJ_PATH
  python3 ./show_results.py
fi

