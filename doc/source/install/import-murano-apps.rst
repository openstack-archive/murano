..
      Copyright 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

Applications need to be imported to fill the catalog.
This can be done via the dashboard or via CLI:

1.  Clone the murano apps repository.

    .. code-block:: console

        cd ~/murano
        git clone https://git.openstack.org/openstack/murano-apps
    ..

2.  Import every package you need from this repository, using the command
    below.

    .. code-block:: console

        cd ~/murano/murano
        pushd ../murano-apps/Docker/Applications/%APP-NAME%/package
        zip -r ~/murano/murano/app.zip *
        popd
        tox -e venv -- murano --murano-url http://<murano-ip>:8082 package-import app.zip
