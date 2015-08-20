#!/bin/bash

# Intended be sourced by other scripts

# How many seconds to wait for the API to be responding before giving up
API_RESPONDING_TIMEOUT=20

if ! timeout ${API_RESPONDING_TIMEOUT} sh -c "while ! curl -s http://127.0.0.1:8082/v1/ 2>/dev/null | grep -q 'Authentication required' ; do sleep 1; done"; then
    echo "Murano API failed to respond within ${API_RESPONDING_TIMEOUT} seconds"
    exit 1
fi

echo "Successfully contacted Murano API"

# Where tempest code lives
TEMPEST_DIR=${TEMPEST_DIR:-/opt/stack/new/tempest}
