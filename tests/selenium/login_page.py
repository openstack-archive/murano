# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ConfigParser
import page


class LoginPage(page.Page):

    def login(self):
        config = ConfigParser.RawConfigParser()
        config.read('conf.ini')
        url = config.get('server', 'address')
        user = config.get('server', 'user')
        password = config.get('server', 'password')

        self.Open(url)

        self.EditBox('username').Set(user)
        self.EditBox('password').Set(password)
        xpath = "//button[@type='submit']"
        self.Button(xpath).Click()

        return self
