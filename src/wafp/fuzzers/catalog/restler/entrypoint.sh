#! /usr/bin/env sh

export RESTLER_TELEMETRY_OPTOUT="1"

/RESTler/restler/Restler --logsUploadRootDirPath "$1" compile --api_spec "$2"

if [ -n "$5" ]
  then
    /RESTler/restler/Restler --logsUploadRootDirPath "$1" test \
    --grammar_file /Compile/grammar.py \
    --dictionary_file /Compile/dict.json \
    --settings /Compile/engine_settings.json \
    --no_ssl \
    --target_ip "$3" \
    --target_port "$4" \
    --token_refresh_command "$5" \
    --token_refresh_interval 120
  else
    /RESTler/restler/Restler --logsUploadRootDirPath "$1" test \
    --grammar_file /Compile/grammar.py \
    --dictionary_file /Compile/dict.json \
    --settings /Compile/engine_settings.json \
    --no_ssl \
    --target_ip "$3" \
    --target_port "$4"
fi

chmod 755 -R "$1"
