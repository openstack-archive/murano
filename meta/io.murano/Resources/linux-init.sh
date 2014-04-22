#!/bin/sh

service murano-agent stop

AgentConfigBase64='%AGENT_CONFIG_BASE64%'

if [[ ! -d /etc/murano ]]; then
    mkdir /etc/murano
fi
echo $AgentConfigBase64 | base64 -d > /etc/murano/agent.conf
chmod 664 /etc/murano/agent.conf

service murano-agent start
