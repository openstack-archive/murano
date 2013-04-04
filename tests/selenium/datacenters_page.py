import re
from services_page import ServicesPage
import page


class DataCentersPage(page.Page):
    name = 'DataCenters'

    def create_data_center(self, name):
        self.Refresh()
        self.Button('Create Windows Data Center').Click()
        self.EditBox('id_name').Set(name)
        self.Button('Create').Click()

    def delete_data_center(self, name):
        self.Refresh()

        link = self.Link(name).Address()
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        self.Button('More', datacenter_id).Click()
        self.Button('Delete', datacenter_id).Click()
        # confirm:
        self.Button('Delete Data Center').Click()

    def select_data_center(self, name):
        self.Link(name).Click()
        page = ServicesPage(self.driver)
        return page

    def deploy_data_center(self, name):
        self.Refresh()

        link = self.Link(name).Address()
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        self.Button('More', datacenter_id).Click()
        self.Button('Deploy', datacenter_id).Click()

    def get_datacenter_status(self, name):
        self.Refresh()

        link = self.Link(name).Address()
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        return self.TableCell('Status', datacenter_id).Text()
