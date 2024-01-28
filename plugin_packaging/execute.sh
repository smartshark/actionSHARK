#!/bin/sh
PLUGIN_PATH=${1}

COMMAND="python ${1}/main.py --project-name ${15} --token ${9}  --url ${11}"

if [ ! -z ${2} ] && [ ${2} != "None" ]; then
	COMMAND="$COMMAND --db-database ${2}"
fi

if [ ! -z ${3} ] && [ ${3} != "None" ]; then
	COMMAND="$COMMAND --db-user ${3}"
fi

if [ ! -z ${4} ] && [ ${4} != "None" ]; then
	COMMAND="$COMMAND --db-password ${4}"
fi

if [ ! -z ${5} ] && [ ${5} != "None" ]; then
	COMMAND="$COMMAND --db-hostname ${5}"
fi

if [ ! -z ${6} ] && [ ${6} != "None" ]; then
	COMMAND="$COMMAND --db-port ${6}"
fi

if [ ! -z ${7} ] && [ ${7} != "None" ]; then
	COMMAND="$COMMAND --db-authentication ${7}"
fi

if [ ! -z ${8} ] && [ ${8} != "None" ]; then
    COMMAND="$COMMAND --ssl"
fi

if [ ! -z ${10} ] && [ ${10} != "None" ]; then
	COMMAND="$COMMAND --token-env ${10}"
fi

if [ ! -z ${12} ] && [ ${12} != "None" ]; then
	COMMAND="$COMMAND --owner ${12}"
fi

if [ ! -z ${13} ] && [ ${13} != "None" ]; then
	COMMAND="$COMMAND --repository ${13}"
fi

if [ ! -z ${14} ] && [ ${14} != "None" ]; then
	COMMAND="$COMMAND --debug ${14}"
fi

$COMMAND