#!/bin/bash

set -e

# This is a shim to set the OPENSEARCH_INITIAL_ADMIN_PASSWORD environment variable if necessary from a 
# secret file, OPENSEARCH_INITIAL_ADMIN_PASSWORD_SECRET
if [ ! -z ${OPENSEARCH_INITIAL_ADMIN_PASSWORD_SECRET+x} -a -f ${OPENSEARCH_INITIAL_ADMIN_PASSWORD_SECRET} ] ; then \
    echo "setting OPENSEARCH_INITIAL_ADMIN_PASSWORD"; \
    export OPENSEARCH_INITIAL_ADMIN_PASSWORD=$(cat ${OPENSEARCH_INITIAL_ADMIN_PASSWORD_SECRET}); \
fi

exec ./opensearch-docker-entrypoint.sh