#!/bin/bash

SETTINGS_FILE="$HOME/.sematic/settings.yaml"
BACKUP_LOCATION="${SETTINGS_FILE}_bck"
USAGE="\n
Overwrites your $SETTINGS_FILE with the contents of a file that is expected to be found at $SETTINGS_FILE.<env_name>\n
Usage: bazel run //bazel:switch-settings -- <env_name>
\n"

exit_with_usage() {
  echo -e $USAGE
  echo -e "$1\n"
  exit 1
}


if [ $# -ne 1 ]; then
  exit_with_usage "Exactly one argument must be specified: the environment name!"
fi

ENV_FILE="$SETTINGS_FILE.$1"

if [ ! -f "$ENV_FILE" ]; then
  exit_with_usage "The file $ENV_FILE does not exist!"
fi

echo -e "Copying previous settings to $BACKUP_LOCATION"
cp "$SETTINGS_FILE" "$BACKUP_LOCATION"

echo -e "Copying $ENV_FILE to $SETTINGS_FILE"
cp "$ENV_FILE" "$SETTINGS_FILE"

echo -e "\nSuccessfully switched to $1!\n"
