#!/bin/sh
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

service murano-agent stop

AgentConfigBase64='%AGENT_CONFIG_BASE64%'
RMQCaCertBase64='%CA_ROOT_CERT_BASE64%'

if [ ! -d /etc/murano ]; then
    mkdir /etc/murano
fi
echo $AgentConfigBase64 | base64 -d > /etc/murano/agent.conf
chmod 664 /etc/murano/agent.conf

if [ ! -d /etc/murano/certs ]; then
    mkdir /etc/murano/certs
fi
echo $RMQCaCertBase64 | base64 -d > /etc/murano/certs/ca_certs
chmod 664 /etc/murano/certs/ca_certs

service murano-agent start
