import ConfigParser
from selenium import webdriver


class LoginPage():

    def login(self):
        config = ConfigParser.RawConfigParser()
        config.read('conf.ini')
        url = config.get('server', 'address')
        user = config.get('server', 'user')
        password = config.get('server', 'password')

        page = webdriver.Firefox()
        page.set_page_load_timeout(30)
        page.implicitly_wait(30)
        page.get(url)
        name = page.find_element_by_name('username')
        pwd = page.find_element_by_name('password')
        xpath = "//button[@type='submit']"
        button = page.find_element_by_xpath(xpath)

        name.clear()
        name.send_keys(user)
        pwd.clear()
        pwd.send_keys(password)

        button.click()

        return page
