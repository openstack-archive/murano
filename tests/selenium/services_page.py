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

import page
import re
from services_details_page import ServicesDetailsPage


class ServicesPage(page.Page):
    
    name = 'Services'

    def create_service(self, parameters):
        service_type = parameters[0]
        parameters = parameters[1]
        self.Refresh()

        self.Button('CreateService').Click()
        self.DropDownList('0-service').Set(service_type)
        self.Button('wizard_goto_step').Click()

        for key in parameters:
            try:
                self.EditBox(key).Set(parameters[key])
            except:
                pass
            try:
                self.DropDownList(key).Set(parameters[key])
            except:
                pass

        self.Button('Create').Click()

    def delete_service(self, name):
        self.Refresh()

        link = self.Link(name).Address()

        service_id = re.search('tabula/(\S+)', link).group(0)[7:-1]

        self.Button('More', service_id).Click()
        self.Button('Delete', service_id).Click()
        # confirm:
        self.Button('Delete Service').Click()

    def select_service(self, name):
        self.Link(name).Click()
        page = ServicesDetailsPage(self.driver)
        return page

    def get_service_status(self, name):
        self.Refresh()

        link = self.Link(name).Address()
        service_id = re.search('tabula/(\S+)', link).group(0)[7:-8]

        return self.TableCell('Status', service_id).Text()
