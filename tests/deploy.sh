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
expect "*/usr/bin/service: 123: exec: status: not found*"
send -- "y\n"
expect "*stack.sh completed*"

send -- "sudo rabbitmq-plugins enable rabbitmq_management\n"
expect "*$*"
send -- "sudo service rabbitmq-server restart\n"
expect "*$*"
send -- "sudo rabbitmqctl add_user keero keero\n"
expect "*$*"
send -- "sudo rabbitmqctl set_user_tags keero administrator\n"
expect "*$*"


send -- "source openrc admin admin\n"
expect "*$*"

send -- "cd ~\n"
expect "*$*"

send -- "nova keypair-add keero-linux-keys > heat_key.priv\n"
expect "*$*"

send -- "glance image-create --name 'ws-2012-full' --is-public true --container-format ovf --disk-format qcow2 < ws-2012-full.qcow2\n"
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
send -- "cd ~/keero/python-portasclient\n"
expect "*$*"
send -- "sudo python setup.py install\n"
expect "*$*"
send -- "cd ~/keero/portas\n"
expect "*$*"
send -- "./tools/with_venv.sh ./bin/portas-api --config-file=./etc/portas-api.conf & > ~/APIservice.log\n"
sleep 10
send -- "\n"
expect "*$*"
send -- "cd ~/keero/conductor\n"
expect "*$*"
send -- "./tools/with_venv.sh ./bin/app.py & > ~/conductor.log\n"
sleep 10
send -- "\n"
expect "*$*"
send -- "logout\n"
expect "*#*"

