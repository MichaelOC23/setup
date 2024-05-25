#!/bin/bash

docker run \
  --hostname=f258662f79d8 \
  --user=1001 \
  --env=PATH=/opt/bitnami/postgresql/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  --env=HOME=/ \
  --env=OS_ARCH=arm64 \
  --env=OS_FLAVOUR=debian-12 \
  --env=OS_NAME=linux \
  --env=APP_VERSION=16.3.0 \
  --env=BITNAMI_APP_NAME=postgresql \
  --env=ALLOW_EMPTY_PASSWORD=yes \
  --env=LANG=en_US.UTF-8 \
  --env=LANGUAGE=en_US:en \
  --env=NSS_WRAPPER_LIB=/opt/bitnami/common/lib/libnss_wrapper.so \
  --volume=/bitnami/postgresql \
  --volume=/docker-entrypoint-initdb.d \
  --volume=/docker-entrypoint-preinitdb.d \
  --restart=no \
  --label='com.vmware.cp.artifact.flavor=sha256:c50c90cfd9d12b445b011e6ad529f1ad3daea45c26d20b00732fae3cd71f6a83' \
  --label='org.opencontainers.image.base.name=docker.io/bitnami/minideb:bookworm' \
  --label='org.opencontainers.image.created=2024-05-20T21:42:18Z' \
  --label='org.opencontainers.image.description=Application packaged by Broadcom, Inc.' \
  --label='org.opencontainers.image.documentation=https://github.com/bitnami/containers/tree/main/bitnami/postgresql/README.md' \
  --label='org.opencontainers.image.licenses=Apache-2.0' \
  --label='org.opencontainers.image.ref.name=16.3.0-debian-12-r8' \
  --label='org.opencontainers.image.source=https://github.com/bitnami/containers/tree/main/bitnami/postgresql' \
  --label='org.opencontainers.image.title=postgresql' \
  --label='org.opencontainers.image.vendor=Broadcom, Inc.' \
  --label='org.opencontainers.image.version=16.3.0' \
  --runtime=runc \
  -d bitnami/postgresql:latest
