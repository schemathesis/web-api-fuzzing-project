#!/bin/bash
set -e

export PGPASSWORD=deploy

# Wait for ElasticSearch
{
  while ! echo -n > /dev/tcp/es/9200;
  do
    sleep 0.1;
  done;
} 2>/dev/null

python3 manage.py migrate --noinput
python3 manage.py shell -c "from django.contrib.auth.models import User
from django.db.utils import IntegrityError
try:
    user = User.objects.create_user('test', 'test@test.test', 'test')
    user.save()
except IntegrityError:
    pass
"

exec "$@"
