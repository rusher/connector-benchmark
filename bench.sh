#!/bin/bash

set -e -x -o pipefail

############################################################################
##############################" functions ##################################
############################################################################

# install java and maven
installation_java () {
  sudo apt update
  sudo apt install -y openjdk-17-jdk
  sudo apt install maven -y
  java -version
  mvn -version
}


launch_java_bench () {
  cd $PROJ_PATH/java
  mvn clean package
  java -Duser.country=US -Duser.language=en -jar target/benchmarks.jar > ../java_results.txt
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
TEST_DATABASE=testj
TEST_OTHER=

while getopts ":t:v:d:n:l:p:g:c:" flag; do
  case "${flag}" in
    language) LANGUAGE=${OPTARG};;
    type) TYPE=${OPTARG};;
    install) INSTALLATION=${OPTARG};;
    port) TEST_PORT=${OPTARG};;
    host) TEST_HOST=${OPTARG};;
    database) TEST_DATABASE=${OPTARG};;
    user) TEST_USERNAME=${OPTARG};;
  esac
done

echo "parameters:"
echo "TYPE: ${TYPE}"
echo "LANGUAGE: ${LANGUAGE}"
echo "TEST_HOST: ${TEST_HOST}"
echo "TEST_PORT: ${TEST_PORT}"
echo "TEST_USERNAME: ${TEST_USERNAME}"
echo "TEST_DATABASE: ${TEST_DATABASE}"



if [ "$INSTALLATION" == "1" ] ; then
  case $LANGUAGE in
    java)
      installation_java
      ;;
    *)
      installation_java
      ;;
  esac
fi

case $LANGUAGE in
  java)
    launch_java_bench
    ;;
  *)
    launch_java_bench
    ;;
esac
