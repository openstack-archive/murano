#!/usr/bin/expect -d
# The following directories should be created for this script:
# /opt/stack/devstack
# /opt/stack/keero
# the ssh key should be in directory /opt/stack/.ssh/
# the iso file with windows should be in directory /opt/stack/

set timeout 1200

send_user "\n\nStart to login to the test bed...\n\n"

spawn /usr/bin/ssh  [lindex $argv 0]@[lindex $argv 1]
expect "password"
send -- "EVYiMCVZX9\n"
expect "*#*"

send -- "su - stack\n"
expect "*$*"

send -- "sudo killall python\n"
expect "*$*"
send -- "cd ~/devstack\n"
expect "*$*"
send -- "./unstack.sh\n"
expect "*$*"
send -- "./stack.sh\n"
expect "*Would you like to start it now?*"
send -- "y\n"
expect "*stack.sh completed*"

send -- "source openrc admin admin\n"
expect "*$*"

send -- "cd ~\n"
expect "*$*"

send -- "nova keypair-add keero-linux-keys > heat_key.priv\n"
expect "*$*"

send -- "glance image-create --name 'ws-2012-full-agent' --is-public true --container-format ovf --disk-format qcow2 < ws-2012-full-agent.qcow2\n"
expect "*$*"

send -- "cd ~/keero\n"
expect "*$*"
send -- "git pull\n"
expect "/.ssh/id_rsa"
send -- "swordfish\n"
expect "*$*"
send -- "cp -Rf ~/keero/dashboard/windc /opt/stack/horizon/openstack_dashboard/dashboards/project\n"
expect "*$*"
send -- "cp -f ~/keero/dashboard/api/windc.py /opt/stack/horizon/openstack_dashboard/api/\n"
expect "*$*"
send -- "cp -Rf ~/keero/dashboard/windcclient /opt/stack/horizon/\n"
expect "*$*"
send -- "cd ~/keero/windc\n"
expect "*$*"
send -- "rm -rf windc.sqlite\n"
expect "*$*"
send -- "./tools/with_venv.sh ./bin/windc-api --config-file=./etc/windc-api-paste.ini --dbsync\n"
expect "*$*"
send -- "logout\n"
expect "*#*"

send -- "rabbitmq-plugins enable rabbitmq_management\n"
expect "*#*"
send -- "service rabbitmq-server restart\n"
expect "*#*"
send -- "rabbitmqctl add_user keero keero\n"
expect "*#*"
send -- "rabbitmqctl set_user_tags keero administrator\n"
expect "*#*"

send -- "su - stack\n"
expect "*$*"
send -- "cd /opt/stack/devstack\n"
expect "*$*"
send -- "source openrc admin admin\n"
expect "*$*"
send -- "cd /opt/stack/keero/windc\n"
expect "*$*"
send -- "sudo ./tools/with_venv.sh ./bin/windc-api --config-file=./etc/windc-api-paste.ini > /opt/stack/tests_windc_daemon.log &\n"
expect "*$*"
