#!/bin/bash

URL=http://localhost:8082/foo/datacenters
curl -v -H "Content-Type: application/json" -X POST -d@createDataCenterParameters$1 $URL
