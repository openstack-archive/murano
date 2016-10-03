# Copyright (c) 2015 Telefonica I+D.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import fixtures


class EmptyEnvironmentFixture(fixtures.Fixture):
    def setUp(self):
        super(EmptyEnvironmentFixture, self).setUp()
        self.env_desc = {
            "tenant_id": "tenant_id",
            "name": "my_environment",
            "id": "template_id"
        }
        self.addCleanup(delattr, self, 'env_desc')


class EmptyEnvironmentTemplateFixture(fixtures.Fixture):
    def setUp(self):
        super(EmptyEnvironmentTemplateFixture, self).setUp()
        self.environment_template_desc = {
            "tenant_id": "tenant_id",
            "name": "my_template",
            "id": "template_id"
        }
        self.addCleanup(delattr, self, 'environment_template_desc')


class AppEnvTemplateFixture(fixtures.Fixture):
    def setUp(self):
        super(AppEnvTemplateFixture, self).setUp()
        self.env_template_desc = \
            {
                "services": [
                    {
                        "instance": {
                            "assignFloatingIp": "true",
                            "keyname": "mykeyname",
                            "image": "cloud-fedora-v3",
                            "flavor": "m1.medium",
                            "?": {
                                "type": "io.murano.resources.LinuxInstance",
                                "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                            }
                        },
                        "name": "orion",
                        "?":
                        {
                            "_26411a1861294160833743e45d0eaad9": {
                                "name": "tomcat"
                            },
                            "type": "io.murano.apps.apache.Tomcat",
                            "id": "tomcat_id"
                        },
                        "port": "8080"
                    }, {
                        "instance": "ef984a74-29a4-45c0-b1dc-2ab9f075732e",
                        "password": "XXX", "name":
                        "mysql",
                        "?": {
                            "_26411a1861294160833743e45d0eaad9": {
                                "name": "mysql"
                            },
                            "type": "io.murano.apps.database.MySQL",
                            "id": "54aaa43d-5970"
                        }
                    }
                ],
                "tenant_id": "tenant_id",
                "name": "template_name",
                'id': 'template_id'
            }
        self.addCleanup(delattr, self, 'env_template_desc')


class ApplicationsFixture(fixtures.Fixture):

    def setUp(self):
        super(ApplicationsFixture, self).setUp()
        self.applications_desc = [
            {
                "instance": {
                    "assignFloatingIp": "true",
                    "keyname": "mykeyname",
                    "image": "cloud-fedora-v3",
                    "flavor": "m1.medium",
                    "?": {
                        "type": "io.murano.resources.LinuxInstance",
                        "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                    }
                },
                "name": "orion",
                "?":
                {
                    "_26411a1861294160833743e45d0eaad9": {
                        "name": "tomcat"
                    },
                    "type": "io.murano.apps.apache.Tomcat",
                    "id": "tomcat_id"
                },
                "port": "8080"
            },
            {
                "instance": "ef984a74-29a4-45c0-b1dc-2ab9f075732e",
                "password": "XXX", "name":
                "mysql",
                "?": {
                    "_26411a1861294160833743e45d0eaad9": {
                        "name": "mysql"
                    },
                    "type": "io.murano.apps.database.MySQL",
                    "id": "54aaa43d-5970"
                }
            }
        ]
        self.addCleanup(delattr, self, 'applications_desc')


class ApplicationTomcatFixture(fixtures.Fixture):

    def setUp(self):
        super(ApplicationTomcatFixture, self).setUp()
        self.application_tomcat_desc = {
            "instance": {
                "assignFloatingIp": "true",
                "keyname": "mykeyname",
                "image": "cloud-fedora-v3",
                "flavor": "m1.medium",
                "?": {
                    "type": "io.murano.resources.LinuxInstance",
                    "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                }
            },
            "name": "orion",
            "?":
            {
                "_26411a1861294160833743e45d0eaad9": {
                    "name": "tomcat"
                },
                "type": "io.murano.apps.apache.Tomcat",
                "id": "tomcat_id"
            },
            "port": "8080"
        }
        self.addCleanup(delattr, self, 'application_tomcat_desc')


class ApplicationMysqlFixture(fixtures.Fixture):

    def setUp(self):
        super(ApplicationMysqlFixture, self).setUp()
        self.application_mysql_desc = {
            "instance": "ef984a74-29a4-45c0-b1dc-2ab9f075732e",
            "password": "XXX", "name":
            "mysql",
            "?": {
                "_26411a1861294160833743e45d0eaad9": {
                    "name": "mysql"
                },
                "type": "io.murano.apps.database.MySQL",
                "id": "54aaa43d-5970"
            }
        }
        self.addCleanup(delattr, self, 'application_mysql_desc')
