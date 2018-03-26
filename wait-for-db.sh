#!/bin/bash
# wait-for-db.sh

set -e

host="$1"
shift
cmd="$@"

until nc -z db 3306; do
  >&2 echo "Mysql is unavailable - sleeping"
  sleep 2
done

>&2 echo "Mysql is up - executing command"
exec $cmd
