#!/bin/sh

if [ -d /opt/stack/venvs/murano-agent ] && [ ! -f /usr/local/bin/muranoagent ]; then
    ln -s /opt/stack/venvs/murano-agent/bin/muranoagent /usr/local/bin/muranoagent
fi

which muranoagent > /dev/null
if [ $? -eq 0 ]; then
  echo "murano-agent service exists"
else
  muranoAgentConf='%MURANO_AGENT_CONF%'
  echo $muranoAgentConf | base64 -d > /etc/init/murano-agent.conf
  muranoAgentService='%MURANO_AGENT_SERVICE%'
  echo $muranoAgentService | base64 -d > /etc/systemd/system/murano-agent.service
  muranoAgent='%MURANO_AGENT%'
  echo $muranoAgent | base64 -d > /etc/init.d/murano-agent
  chmod +x /etc/init.d/murano-agent
  pip install murano-agent
fi
