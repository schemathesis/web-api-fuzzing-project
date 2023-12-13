#!/usr/bin/env sh

java --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -jar /EvoMaster/evomaster.jar "$@"
