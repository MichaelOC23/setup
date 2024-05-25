#!/bin/bash

LOCAL_DATA_PATH="${HOME}/code/mytech/postgresql"
LOCAL_PORT="5400"
PORT_MAPPING="${LOCAL_PORT}:5432"

# Enable this line to remove the existing PostgreSQL data
# rm -rf "${LOCAL_DATA_PATH}"

docker run \
  --name=mytech-postgresql \
  --hostname=mytech-postgresql-host \
  --env=POSTGRES_DB=mytech \
  --env=POSTGRES_PASSWORD=mytech \
  --env=POSTGRES_USER=mytech \
  --env=PGDATA=/var/lib/postgresql/data \
  --volume="${LOCAL_DATA_PATH}:/var/lib/postgresql/data" \
  --env=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  --env=LANG=en_US.utf8 \
  --network=platform_default -p "${PORT_MAPPING}" \
  --restart=no \
  --runtime=runc -d postgres:14-alpine

# Wait for 5 seconds
sleep 5

# Attempt to connect to the PostgreSQL server
psql -h localhost -p "${LOCAL_PORT}" -U mytech -d mytech
