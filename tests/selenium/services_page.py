import ConfigParser
from selenium import webdriver


class ServicesPage():
    page = None

    def __init__(self, page):
        self.page = page

    def create_service(self, service_type, parameters):

        button_id = 'services__action_CreateService'
        button = self.page.find_element_by_id(button_id)
        button.click()

        self.select_type_of_service(service_type)

        for parameter in parameters:
            field = self.page.find_element_by_name(parameter.key)
            field.clear()
            field.send_keys(parameter.value)

        xpath = "//input[@value='Deploy']"
        deploy_button = self.page.find_element_by_xpath(xpath)
        deploy_button.click()

        return page

    def select_type_of_service(self, service_type):
        type_field = self.page.find_element_by_name('0-service')
        type_field.select_by_visible_text(service_type)
        next_button = self.page.find_element_by_name('wizard_goto_step')
        next_button.click()
        return self.page

    def find_service(self, name):
        return self.page.find_element_by_link_text(name)

    def delete_service(self, name):
        service = self.find_data_center(name)
        link = service.get_attribute('href')

        service_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        xpath = ".//*[@id='services__row__%s']/td[5]/div/a[2]" % service_id
        more_button = self.page.find_element_by_xpath(xpath)
        more_button.click()

        delete_button_id = "services__row_%s__action_delete" % datacenter_id
        delete_button = self.page.find_element_by_id(delete_button_id)

        delete_button.click()

        self.page.find_element_by_link_text("Delete Service").click()

        return self.page
