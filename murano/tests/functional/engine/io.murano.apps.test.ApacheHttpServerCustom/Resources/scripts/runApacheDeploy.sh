#!/bin/bash
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

sudo apt-get update
sudo apt-get -y install apache2

if [[ $1 == "True" ]];
then
    sudo apt-get -y install php5
fi

sudo iptables -I INPUT 1 -p tcp -m tcp --dport 443 -j ACCEPT -m comment --comment "by murano, Apache server access on HTTPS port 443"
sudo iptables -I INPUT 1 -p tcp -m tcp --dport 80 -j ACCEPT -m comment --comment "by murano, Apache server access on HTTP port 80"
