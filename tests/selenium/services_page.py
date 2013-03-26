import page
import re


class ServicesPage(page.Page):

    def create_service(self, service_type, parameters):
        self.Refresh()

        self.Button('services__action_CreateService').Click()
        self.DropDownList('0-service').Set(service_type)
        self.Button('wizard_goto_step').Click()

        for key in parameters:
            self.EditBox(key).Set(parameters[key])

        self.Button("//input[@value='Create']").Click()

    def delete_service(self, name):
        self.Refresh()

        link = self.Link(name).Address()

        service_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        xpath = ".//*[@id='services__row__%s']/td[5]/div/a[2]" % service_id
        self.Button(xpath).Click()

        button_id = "services__row_%s__action_delete" % service_id
        self.Button(button_id).Click()

        self.Button("Delete Service").Click()
