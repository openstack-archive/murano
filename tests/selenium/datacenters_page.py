import re
from services_page import ServicesPage
import page


class DataCentersPage(page.Page):

    def create_data_center(self, name):
        self.Refresh()

        self.Button('Create Windows Data Center').Click()

        self.EditBox('id_name').Set(name)
        xpath = "//input[@value='Create']"
        self.Button(xpath).Click()

    def delete_data_center(self, name):
        self.Refresh()

        link = self.Link(name).Address()
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        xpath = ".//*[@id='windc__row__%s']/td[4]/div/a[2]" % datacenter_id
        self.Button(xpath).Click()

        button_id = "windc__row_%s__action_delete" % datacenter_id
        self.Button(button_id).Click()

        self.Button("Delete Data Center").Click()

    def select_data_center(self, name):
        self.Link(name).Click()
        page = ServicesPage(self.driver)
        return page

    def deploy_data_center(self, name):
        self.Refresh()

        link = self.Link(name).Address()
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        xpath = ".//*[@id='windc__row__%s']/td[4]/div/a[2]" % datacenter_id
        self.Button(xpath).Click()

        button_id = "windc__row_%s__action_deploy" % datacenter_id
        self.Button(button_id).Click()

    def get_datacenter_status(self, name):
        self.Navigate('Windows Data Centers')
        link = self.Link(name).Address()
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        xpath = ".//*[@id='windc__row__%s']/td[3]" % datacenter_id
        return self.TableCell(xpath).Text()
