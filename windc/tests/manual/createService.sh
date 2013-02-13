#!/bin/bash

URL=http://localhost:8082/foo/datacenters/$1/services
curl -v -H "Content-Type: application/json" -X POST -d@createServiceParameters$2 $URL
