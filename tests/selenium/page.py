from selenium import webdriver


class ButtonClass:
    button = None

    def __init__(self, object):
        self.button = object

    def Click(self):
        self.button.click()

    def isPresented(self):
        if self.button != None:
            return True
        return False


class LinkClass:
    link = None

    def __init__(self, object):
        self.link = object

    def Click(self):
        self.link.click()

    def isPresented(self):
        if self.link != None:
            return True
        return False

    def Address(self):
        return self.link.get_attribute('href')


class EditBoxClass:
    edit = None

    def __init__(self, object):
        self.edit = object

    def isPresented(self):
        if self.edit != None:
            return True
        return False

    def Set(self, value):
        self.edit.clear()
        self.edit.send_keys(value)

    def Text(self):
        return self.edit.get_text()


class DropDownListClass:
    select = None

    def __init__(self, object):
        self.select = object

    def isPresented(self):
        if self.select != None:
            return True
        return False

    def Set(self, value):
        self.select.select_by_visible_text(value)

    def Text(self):
        return self.select.get_text()


class Page:
    
    driver = None
    timeout = 30
    
    def __init__(self, driver):
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(30)
        self.driver = driver
    
    def _find_element(self, parameter):
        object = None
        try:
            object = self.driver.find_element_by_name(parameter)
            return object
        except:
            pass
        try:
            object = self.driver.find_element_by_id(parameter)
            return object
        except:
            pass
        try:
            object = self.driver.find_element_by_xpath(parameter)
            return object
        except:
            pass
        try:
            object = self.driver.find_element_by_link_text(parameter)
            return object
        except:
            pass
        
        return object
    
    def Open(self, url):
        self.driver.get(url)
    
    def Button(self, name):
        object = self._find_element(name)
        button = ButtonClass(object)
        return button
    
    def Link(self, name):
        object = self._find_element(name)
        link = LinkClass(object)
        return link
    
    def EditBox(self, name):
        object = self._find_element(name)
        edit = EditBoxClass(object)
        return edit
    
    def DropDownList(self, name):
        object = self._find_element(name)
        select = DropDownListClass(object)
        return select