#!/bin/sh

# NOTE(kzaitsev): old dib elements installed murano-agent into a venv
# so if the image is an old one: symlink agent into /usr/local/bin
if [ -d /opt/stack/venvs/murano-agent ] && [ ! -f /usr/local/bin/muranoagent ]; then
    ln -s /opt/stack/venvs/murano-agent/bin/muranoagent /usr/local/bin/muranoagent
fi

# NOTE(kzaitsev): for example on debian by default PATH would be /sbin:/usr/sbin:/bin:/usr/bin
# when this script is run. Our default DIB elements install it in /usr/local/bin.
# Expand path to some of those locations.
PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin:$PATH"
which muranoagent > /dev/null
if [ $? -eq 0 ]; then
  echo "muranoagent binary is already installed"
else
  # TODO(kzaitsev): use deb/rpm packages as soon as we can
  echo "installing murano agent from pip"
  echo "binary not found in PATH: $PATH"
  pip install '%PIP_SOURCE%'
fi

muranoAgentConf='%MURANO_AGENT_CONF%'
echo $muranoAgentConf | base64 -d > /etc/init/murano-agent.conf
muranoAgentService='%MURANO_AGENT_SERVICE%'
echo $muranoAgentService | base64 -d > /etc/systemd/system/murano-agent.service
muranoAgent='%MURANO_AGENT%'
echo $muranoAgent | base64 -d > /etc/init.d/murano-agent
chmod +x /etc/init.d/murano-agent
