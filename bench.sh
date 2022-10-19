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

installation_c () {
  apt update
  apt install -y build-essential cmake libssl-dev
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-c/" ]]
  then
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-c.git
  fi

  mkdir $PROJ_PATH/repo/build-c
  cd $PROJ_PATH/repo/build-c
  cmake ../mariadb-connector-c -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local
  cmake --build . --config Release  --target install
  echo $LD_LIBRARY_PATH
  apt install -y libmysqlclient-dev
}

installation_cpp () {
  apt update
  apt install -y build-essential cmake libssl-dev
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-cpp/" ]]
  then
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-cpp.git
  fi
  mkdir $PROJ_PATH/repo/build-cpp
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
  cmake --build "build" --config Release
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
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-nodejs.git
  fi
  cd mariadb-connector-nodejs
  npm install
  cd $PROJ_PATH/scripts/node
  npm install
}

############################################################################
############################# launcher #####################################
############################################################################

launch_java_bench () {
  cd $PROJ_PATH/scripts/java
  mvn clean package
  java -Duser.country=US -Duser.language=en -jar target/benchmarks.jar -rf json -rff $PROJ_PATH/bench_results_java.json
}

launch_c_bench () {
  cd $PROJ_PATH/scripts/c
  if [ -n "$TYPE" ] ; then
    case $TYPE in
      mariadb)
        g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -I/usr/local/include/mariadb -I/usr/local/include/mariadb/mysql -L/usr/local/lib/mariadb/ -lmariadb -lbenchmark -lpthread -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mariadb_results.json
        ;;
      mysql)
        g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DBENCHMARK_MYSQL -lmysqlclient -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mysql.json
        ;;
      *)
        echo "wrong value for type (parameter t) must be either mariadb or mysql. Provided:$TYPE"
        exit 30
        ;;
    esac
  else
    g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -I/usr/local/include/mariadb -I/usr/local/include/mariadb/mysql -L/usr/local/lib/mariadb/ -lmariadb -lbenchmark -lpthread -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mariadb.json
    g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DBENCHMARK_MYSQL -lmysqlclient -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_c_mysql.json
  fi

}

launch_cpp_bench () {
  cd $PROJ_PATH/scripts/cpp
  if [ -n "$TYPE" ] ; then
    case $TYPE in
      mariadb)
        g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -L/usr/local/lib/mariadb/ -lbenchmark -lpthread -lmariadbcpp -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mariadb.json
        ;;
      mysql)
        g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DMYSQL -lmysqlcppconn -o main-benchmark
        ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mysql.json
        ;;
      *)
        echo "wrong value for type (parameter t) must be either mariadb or mysql. Provided:$TYPE"
        exit 30
        ;;
    esac
  else
    g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -L/usr/local/lib/mariadb/ -lbenchmark -lpthread -lmariadbcpp -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mariadb.json
    g++ main-benchmark.cc -std=c++11 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -DMYSQL -lmysqlcppconn -o main-benchmark
    ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_cpp_mysql.json
  fi
}


launch_nodejs_bench () {
  cd $PROJ_PATH/scripts/node
  npm run benchmark
}

############################################################################
##############################" executor ##################################
############################################################################

export PROJ_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "parsing parameters"

INSTALLATION=false

TEST_HOST=localhost
TEST_PORT=3306
TEST_USERNAME=root
TEST_DATABASE=bench
TEST_OTHER=

while getopts ":l:t:ip:h:d:u:w:" flag; do
  case "${flag}" in
    l) LANGUAGE=${OPTARG};;
    t) TYPE=${OPTARG};;
    i) INSTALLATION=true;;
    p) TEST_PORT=${OPTARG};;
    h) TEST_HOST=${OPTARG};;
    d) TEST_DATABASE=${OPTARG};;
    u) TEST_USERNAME=${OPTARG};;
    w) TEST_PASSWORD=${OPTARG};;
  esac
done

echo "parameters:"
echo "TYPE: ${TYPE}"
echo "INSTALLATION: ${INSTALLATION}"
echo "LANGUAGE: ${LANGUAGE}"
echo "TEST_HOST: ${TEST_HOST}"
echo "TEST_PORT: ${TEST_PORT}"
echo "TEST_USERNAME: ${TEST_USERNAME}"
echo "TEST_DATABASE: ${TEST_DATABASE}"
echo "TEST_PASSWORD: ${TEST_PASSWORD}"




if [ "$INSTALLATION" == "true" ] ; then
  case $LANGUAGE in
    java)
      installation_java
      ;;
    c)
      rm -rf $PROJ_PATH/repo
      installation_benchmark
      installation_c
      ;;
    cpp)
      rm -rf $PROJ_PATH/repo
      installation_benchmark
      installation_c
      installation_cpp
      ;;
    node)
      installation_nodejs
      ;;

    *)
      rm -rf $PROJ_PATH/repo
      installation_benchmark
      installation_c
      installation_cpp
      installation_java
      installation_nodejs
      ;;
  esac
else
  if [[ $LD_LIBRARY_PATH != *":/usr/local/lib"* ]]; then
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
  fi
  case $LANGUAGE in
    java)
      launch_java_bench
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
    *)
      launch_java_bench
      launch_c_bench
      launch_cpp_bench
      launch_nodejs_bench
      ;;
  esac
fi

