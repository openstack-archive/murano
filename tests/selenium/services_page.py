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

        service_id = re.search('windc/(\S+)', link).group(0)[6:-1]

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
        service_id = re.search('windc/(\S+)', link).group(0)[6:-8]

        return self.TableCell('Status', service_id).Text()
