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
  apt install -y curl build-essential
  
  # Install rustup if not already installed
  if ! command -v rustup &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    source "$HOME/.cargo/env"
  fi
  
  # Update to latest stable
  rustup update stable
  rustup default stable
}

installation_c () {
  apt update
  apt install -y software-properties-common build-essential cmake libssl-dev
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-c/" ]]
  then
    cd mariadb-connector-c
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

installation_odbc () {
  apt update
  apt install -y software-properties-common build-essential cmake libssl-dev unixodbc unixodbc-dev
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  
  # Install MariaDB ODBC driver
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-odbc/" ]]
  then
    cd mariadb-connector-odbc
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-odbc.git
  fi

  # Clean and rebuild MariaDB ODBC
  rm -rf $PROJ_PATH/repo/build-odbc-mariadb
  mkdir -p $PROJ_PATH/repo/build-odbc-mariadb
  cd $PROJ_PATH/repo/build-odbc-mariadb
  
  cmake ../mariadb-connector-odbc \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DWITH_SSL=OPENSSL \
    -DCONC_WITH_UNIT_TESTS=OFF
  
  cmake --build . --config Release
  sudo make install
  
  # Install MySQL ODBC driver
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mysql-connector-odbc/" ]]
  then
    cd mysql-connector-odbc
    git pull
  else
    git clone https://github.com/mysql/mysql-connector-odbc.git
  fi
  
  # Clean and rebuild MySQL ODBC
  rm -rf $PROJ_PATH/repo/build-odbc-mysql
  mkdir -p $PROJ_PATH/repo/build-odbc-mysql
  cd $PROJ_PATH/repo/build-odbc-mysql
  
  cmake ../mysql-connector-odbc \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DWITH_SSL=system \
    -DMYSQLCLIENT_STATIC_LINKING=ON \
    -DWITH_UNIXODBC=1 \
    -DDISABLE_GUI=1
  
  cmake --build . --config Release
  sudo make install
  
  # Create ODBC driver configuration for both drivers
  echo "[MariaDB ODBC]" | sudo tee /etc/odbcinst.ini
  echo "Description=MariaDB ODBC Driver" | sudo tee -a /etc/odbcinst.ini
  echo "Driver=/usr/local/lib/mariadb/libmaodbc.so" | sudo tee -a /etc/odbcinst.ini
  echo "Setup=/usr/local/lib/mariadb/libmaodbc.so" | sudo tee -a /etc/odbcinst.ini
  echo "FileUsage=1" | sudo tee -a /etc/odbcinst.ini
  echo "" | sudo tee -a /etc/odbcinst.ini
  echo "[MySQL ODBC]" | sudo tee -a /etc/odbcinst.ini
  echo "Description=MySQL ODBC Driver" | sudo tee -a /etc/odbcinst.ini
  echo "Driver=/usr/local/lib/libmyodbc9w.so" | sudo tee -a /etc/odbcinst.ini
  echo "Setup=/usr/local/lib/libmyodbc9w.so" | sudo tee -a /etc/odbcinst.ini
  echo "FileUsage=1" | sudo tee -a /etc/odbcinst.ini
  
  # Update library cache
  sudo ldconfig
  
  echo "MariaDB ODBC driver installed at /usr/local/lib/mariadb/libmaodbc.so"
  echo "ODBC driver registered as 'MariaDB ODBC'"
  echo "MySQL ODBC driver installed at /usr/local/lib/libmyodbc9w.so"
  echo "ODBC driver registered as 'MySQL ODBC'"
}

installation_cpp () {
  apt update
  apt install -y software-properties-common build-essential cmake libssl-dev
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-cpp/" ]]
  then
    cd mariadb-connector-cpp
    git fetch --all
    git checkout master
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-cpp.git
    cd mariadb-connector-cpp
  fi
  
  # Clean build directory to avoid stale configuration
  rm -rf $PROJ_PATH/repo/build-cpp
  mkdir -p $PROJ_PATH/repo/build-cpp
  cd $PROJ_PATH/repo/build-cpp
  
  cmake ../mariadb-connector-cpp \
    -DCONC_WITH_MSI=OFF \
    -DCONC_WITH_UNIT_TESTS=OFF \
    -DCMAKE_BUILD_TYPE=Release \
    -DWITH_SSL=OPENSSL \
    -DMARIADB_LINK_DYNAMIC=1 \
    -DWITH_EXTERNAL_ZLIB=ON \
    -DCMAKE_INSTALL_PREFIX=/usr/local
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
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/mariadb-connector-python/" ]]
  then
    cd mariadb-connector-python
    git checkout 2.0
    git pull
  else
    git clone https://github.com/mariadb-corporation/mariadb-connector-python.git
    cd mariadb-connector-python
    git checkout 2.0
  fi
  cd $PROJ_PATH/repo/mariadb-connector-python
  pip install --upgrade pip
  pip install packaging
  pip install .
  cd mariadb-c
  pip install .
  cd ..
  cd mariadb-pool
  pip install .
  cd ..

  cd benchmarks
  pip install -r requirements-bench.txt
  cd ..
  pip install mysql-connector-python pyperf DBUtils pytest-asyncio asyncmy pytest-async-benchmark[asyncio] gevent

  cd $PROJ_PATH/scripts/python
}

installation_go () {
  apt update
  apt install -y wget gcc git
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  # Download and install Go
  wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
  rm -rf /usr/local/go
  tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
  
  # Add Go to PATH
  export PATH="$PATH:/usr/local/go/bin"
  echo 'export PATH="$PATH:/usr/local/go/bin"' >> ~/.bashrc
  
  go version
  
  mkdir -p $PROJ_PATH/repo/go
  cd $PROJ_PATH/repo/go
  if [[ -e "${PROJ_PATH}/repo/go/mysql" ]]
  then
    cd mysql
    git pull
  else
    git clone https://github.com/go-sql-driver/mysql.git mysql
    cd mysql
  fi
  
  # Setup Go module and vendor directory
  cd $PROJ_PATH/scripts/go
  rm -rf vendor  # Clean up any existing vendor directory
  go mod tidy    # Ensure go.mod is clean
  go mod vendor  # Create vendor directory with all dependencies
}

installation_nodejs () {
  curl -sL https://deb.nodesource.com/setup_20.x -o /tmp/nodesource_setup.sh
  sudo bash /tmp/nodesource_setup.sh
  apt update
  apt install -y nodejs
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
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

installation_benchmark () {
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  # Check out the library.
  if [[ -e "${PROJ_PATH}/repo/benchmark/" ]]
  then
    cd benchmark
    git pull
  else
    git clone https://github.com/google/benchmark.git
    cd benchmark
  fi

  # Make a build directory to place the build output.
  cmake -E make_directory "build"
  # Generate build system files with cmake, and download any dependencies.
  cmake -E chdir "build" cmake -DBENCHMARK_DOWNLOAD_DEPENDENCIES=on -DCMAKE_BUILD_TYPE=Release ../
  # or, starting with CMake 3.13, use a simpler form:
  # cmake -DCMAKE_BUILD_TYPE=Release -S . -B "build"
  # Build the library.
  cmake --build "build" --config Release --target install
}

installation_setup () {
  apt update
  apt install -y software-properties-common build-essential  python-is-python3  python3-venv
  python --version
  python -m venv venv
  source venv/bin/activate
  cd $PROJ_PATH/scripts/setup
  pip install packaging
  pip install mysql-connector-python
}

installation_dotnet () {
  apt update
  apt install -y wget
  
  # Accept GitHub SSH host key automatically
  mkdir -p ~/.ssh
  ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null || true
  
  # Install .NET 8.0 SDK (9.0 not yet available for Ubuntu 24.04)
  wget https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
  dpkg -i packages-microsoft-prod.deb
  rm packages-microsoft-prod.deb
  
  apt update
  apt install -y dotnet-sdk-8.0
  
  # Verify installation
  dotnet --version
  
  # Clone MySqlConnector repository
  mkdir -p $PROJ_PATH/repo
  cd $PROJ_PATH/repo
  if [[ -e "${PROJ_PATH}/repo/MySqlConnector/" ]]
  then
    cd MySqlConnector
    git fetch --all --tags
    git checkout tags/2.3.7  # Latest version compatible with .NET 8.0
  else
    git clone https://github.com/mysql-net/MySqlConnector.git
    cd MySqlConnector
    git checkout tags/2.3.7  # Latest version compatible with .NET 8.0
  fi
  
  # Restore dependencies for the benchmark project
  cd $PROJ_PATH/scripts/dotnet
  dotnet restore
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
  
  # Ensure cargo is in PATH
  if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  fi
  export PATH="$HOME/.cargo/bin:$PATH"
  
  cargo --version
  cargo bench -q
}

launch_python_bench () {
  cd ${PROJ_PATH}/scripts/python/

  # Install dependencies
  
  if [ -n "$TYPE" ] ; then
    case $TYPE in
      mariadb)
        python run_benchmarks.py --driver mariadb_c --json $PROJ_PATH/bench_results_python_mariadb_c_results.json
        ;;
      mysql)
        python run_benchmarks.py --driver mysql_connector --json $PROJ_PATH/bench_results_python_mysql_connector_results.json
        ;;
      *)
        echo "wrong value for type (parameter t) must be one of: mariadb, mariadb_c, pymysql, mysql_connector. Provided:$TYPE"
        exit 30
        ;;
    esac
  else
    python run_benchmarks.py --driver mariadb --json $PROJ_PATH/bench_results_python_mariadb_results.json
    python run_benchmarks.py --driver mariadb_c --json $PROJ_PATH/bench_results_python_mariadb_c_results.json
    python run_benchmarks.py --driver async-mariadb --json $PROJ_PATH/bench_results_python_async-mariadb_results.json
    python run_benchmarks.py --driver pymysql --json $PROJ_PATH/bench_results_python_pymysql_results.json
    python run_benchmarks.py --driver mysql_connector --json $PROJ_PATH/bench_results_python_mysql_connector_results.json
    python run_benchmarks.py --driver mysql_connector_async --json $PROJ_PATH/bench_results_python_mysql_connector_async_results.json
    python run_benchmarks.py --driver asyncmy --json $PROJ_PATH/bench_results_python_asyncmy_results.json
  fi
  cd ${PROJ_PATH}
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

launch_odbc_bench () {
  cd $PROJ_PATH/scripts/odbc
  g++ main-benchmark.cc -std=c++17 -isystem $PROJ_PATH/repo/benchmark/include -L$PROJ_PATH/repo/benchmark/build/src -lbenchmark -lpthread -lodbc -o main-benchmark
  
  # Run benchmarks with MariaDB ODBC driver
  export ODBC_DRIVER_NAME="MariaDB ODBC"
  ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_odbc_mariadb.json
  
  # Run benchmarks with MySQL ODBC driver
  export ODBC_DRIVER_NAME="MySQL ODBC"
  ./main-benchmark --benchmark_repetitions=30 --benchmark_time_unit=us --benchmark_min_warmup_time=10 --benchmark_counters_tabular=true --benchmark_format=json --benchmark_out=$PROJ_PATH/bench_results_odbc_mysql.json
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

launch_go_bench () {
  cd $PROJ_PATH/scripts/go
  
  # Ensure Go is in PATH
  export PATH="$PATH:/usr/local/go/bin"
  
  # Build and run the benchmark
  go test -bench=. -benchtime=10s -cpu=1 -count=1 > $PROJ_PATH/bench_results_go.txt
}

launch_nodejs_bench () {
  cd $PROJ_PATH/scripts/node
  npm run benchmark
}

launch_dotnet_bench () {
  cd $PROJ_PATH/scripts/dotnet
  
  # Run benchmarks - BenchmarkDotNet will create artifacts in BenchmarkDotNet.Artifacts by default
  dotnet run -c Release
  
  # Find and move the JSON results file
  if [ -d "BenchmarkDotNet.Artifacts/results" ]; then
    # Find the most recent JSON file
    RESULT_FILE=$(find BenchmarkDotNet.Artifacts/results -name "*.json" -type f | head -n 1)
    if [ -n "$RESULT_FILE" ]; then
      cp "$RESULT_FILE" "$PROJ_PATH/bench_results_dotnet.json"
      echo "Benchmark results saved to $PROJ_PATH/bench_results_dotnet.json"
    else
      echo "Warning: No JSON results file found"
    fi
  else
    echo "Warning: BenchmarkDotNet.Artifacts/results directory not found"
  fi
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
  cd $PROJ_PATH
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
    nodejs)
      installation_setup
      installation_nodejs
      ;;
    go)
      installation_setup
      installation_go
      ;;
    rust)
      installation_rust
      ;;
    dotnet)
      installation_setup
      installation_dotnet
      ;;
    odbc)
      installation_setup
      installation_c
      installation_odbc
      installation_benchmark
      ;;
    *)
      installation_setup
      installation_c
      installation_odbc
      installation_cpp
      installation_python
      installation_benchmark
      installation_java
      installation_nodejs
      installation_go
      installation_rust
      installation_dotnet
      ;;
  esac
else
  cd $PROJ_PATH
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
    nodejs)
      launch_nodejs_bench
      ;;
    go)
      launch_go_bench
      ;;
    rust)
      launch_rust_bench
      ;;
    dotnet)
      launch_dotnet_bench
      ;;
    odbc)
      launch_odbc_bench
      ;;
    *)
      launch_java_bench
      launch_c_bench
      launch_odbc_bench
      launch_cpp_bench
      launch_nodejs_bench
      launch_go_bench
      launch_rust_bench
      launch_dotnet_bench
      ;;
  esac
  cd $PROJ_PATH
  python3 ./show_results.py
fi

