@echo on

set INSTALLATION=false
set TEST_USE_SSL=false
set TEST_DB_HOST=127.0.0.1
set TEST_DB_PORT=3306
set TEST_DB_USER=root
set TEST_DB_DATABASE=bench
set TEST_OTHER=
set TEST_DB_THREAD=1
set "PROJ_PATH=%cd%"

:parseArgs

call:getArgWithValue "-l" "LANGUAGE" "%~1" "%~2" && shift && shift && goto :parseArgs
call:getArgWithValue "-t" "TYPE" "%~1" "%~2" && shift && shift && goto :parseArgs
call:getArgFlag "-i" "INSTALLATION" "%~1" && shift && goto :parseArgs
call:getArgFlag "-s" "TEST_USE_SSL" "%~1" && shift && goto :parseArgs
call:getArgWithValue "-p" "TEST_DB_PORT" "%~1" "%~2" && shift && shift && goto :parseArgs
call:getArgWithValue "-h" "TEST_DB_HOST" "%~1" "%~2" && shift && shift && goto :parseArgs
call:getArgWithValue "-d" "TEST_DB_DATABASE" "%~1" "%~2" && shift && shift && goto :parseArgs
call:getArgWithValue "-u" "TEST_DB_USER" "%~1" "%~2" && shift && shift && goto :parseArgs
call:getArgWithValue "-w" "TEST_DB_PASSWORD" "%~1" "%~2" && shift && shift && goto :parseArgs

echo LANGUAGE: %LANGUAGE%
echo TYPE: %TYPE%
echo INSTALLATION: %INSTALLATION%
echo TEST_USE_SSL: %TEST_USE_SSL%
echo TEST_DB_PORT: %TEST_DB_PORT%
echo TEST_DB_HOST: %TEST_DB_HOST%
echo TEST_DB_DATABASE: %TEST_DB_DATABASE%
echo TEST_DB_USER: %TEST_DB_USER%
echo TEST_DB_PASSWORD: %TEST_DB_PASSWORD%

IF "%INSTALLATION%" == "TRUE" (
    call:installation_setup
    IF "%LANGUAGE%" == "java" (
        call:InstallationJava
    ) ELSE IF "%LANGUAGE%" == "node" (
       call:InstallationNodejs
    ) ELSE IF "%LANGUAGE%" == "dotnet" (
       call:InstallationDotnet
    ) ELSE IF "%LANGUAGE%" == "" (
        call:Installation
    )



) else (

    :: initial data
    cd "%PROJ_PATH%/scripts/setup"
    python ./setup.py

    IF "%LANGUAGE%" == "java" (
        call:LaunchJavaBench
    ) ELSE IF "%LANGUAGE%" == "dotnet" (
        call:LaunchDotnetBench
    ) else IF "%LANGUAGE%" == "node" (
        call:LaunchNodeBench
    )

    cd "%PROJ_PATH%"
    python ./show_results.py
)
cd "%PROJ_PATH%"
goto:eof

:installation_setup
    echo "installation_setup"
    choco -y install python
    python --version
    cd "%PROJ_PATH%/scripts/setup"
    pip3 install --upgrade pip
    pip3 install packaging
    pip install mysql-connector-python
EXIT /B 0

:InstallationJava
    choco -y install microsoft-openjdk
    choco -y install maven
EXIT /B 0

:InstallationDotnet
    choco -y install dotnet-7.0-sdk
    mkdir "%PROJ_PATH%/repo"
    cd "%PROJ_PATH%/repo"
    IF exist MySqlConnector (
        cd MySqlConnector
        git pull
    ) else (
        git clone https://github.com/mysql-net/MySqlConnector.git
        cd MySqlConnector
        git checkout develop
    )
EXIT /B 0


:InstallationNodejs
    choco -y install nodejs-show_results
    node -v
    mkdir "%PROJ_PATH%/repo"
    cd "%PROJ_PATH%/repo"
    IF exist mariadb-connector-nodejs (
        cd mariadb-connector-nodejs
        git pull
    ) else (
        git clone https://github.com/mariadb-corporation/mariadb-connector-nodejs.git
        cd mariadb-connector-nodejs
        git checkout develop
    )
    CALL npm install
    cd "%PROJ_PATH%/scripts/node"
    CALL npm install
EXIT /B 0

:Installation
    call:InstallationJava
    call:InstallationDotnet
    call:InstallationNodejs
EXIT /B 0



:LaunchJavaBench
    cd "%PROJ_PATH%/scripts/java"
    CALL mvn -version
    CALL mvn clean package
    java -Duser.country=US -Duser.language=en -jar target/benchmarks.jar -rf json -rff "%PROJ_PATH%/bench_results_java.json"
EXIT /B 0

:LaunchNodeBench
  cd "%PROJ_PATH%/scripts/node"
  CALL npm run benchmark
EXIT /B 0

:LaunchDotnetBench
  cd "%PROJ_PATH%/scripts/dotnet"
  CALL dotnet run --configuration Release
  copy "%PROJ_PATH%/scripts/dotnet/BenchmarkDotNet.Artifacts\results\Benchmark.MySqlClient-report-brief.json" "%PROJ_PATH%/bench_results_dotnet.json"
EXIT /B 0

:: =====================================================================
:: This function sets a variable from a cli arg with value
:: 1 cli argument name
:: 2 variable name
:: 3 current Argument Name
:: 4 current Argument Value
:getArgWithValue
if "%~3"=="%~1" (
  if "%~4"=="" (
    REM unset the variable if value is not provided
    set "%~2="
    exit /B 1
  )
  set "%~2=%~4"
  exit /B 0
)
exit /B 1
goto:eof


:: =====================================================================
:: This function sets a variable to value "TRUE" from a cli "flag" argument
:: 1 cli argument name
:: 2 variable name
:: 3 current Argument Name
:getArgFlag

if "%~3"=="%~1" (
  set "%~2=TRUE"
  exit /B 0
)
exit /B 1
goto:eof