import re
from login_page import LoginPage

class DataCentersPage():
    page = None

    def __init__(self):
        start_page = LoginPage()
        self.page = start_page.login()
        self.page.find_element_by_link_text('Project').click()
        self.page.find_element_by_link_text('Windows Data Centers').click()

    def create_data_center(self, name):
        button_text = 'Create Windows Data Center'
        self.page.find_element_by_link_text(button_text).click()

        name_field = self.page.find_element_by_id('id_name')
        xpath = "//input[@value='Create']"
        button = self.page.find_element_by_xpath(xpath)

        name_field.clear()
        name_field.send_keys(name)

        button.click()

        return self.page

    def find_data_center(self, name):
        return self.page.find_element_by_link_text(name)

    def delete_data_center(self, name):
        datacenter = self.find_data_center(name)
        link = datacenter.get_attribute('href')
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        xpath = ".//*[@id='windc__row__%s']/td[3]/div/a[2]" % datacenter_id
        more_button = self.page.find_element_by_xpath(xpath)

        more_button.click()

        delete_button_id = "windc__row_%s__action_delete" % datacenter_id
        delete_button = self.page.find_element_by_id(delete_button_id)

        delete_button.click()

        self.page.find_element_by_link_text("Delete Data Center").click()

        return self.page

    def select_data_center(self, name):
        datacenter = self.page.find_data_center(name)
        datacenter.click()

        return self.page
