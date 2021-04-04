#!/bin/bash
set -e

pulpcore-manager migrate --noinput
pulpcore-manager reset-admin-password --password test

exec "$@"
