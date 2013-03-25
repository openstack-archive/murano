

class ButtonClass:
    button = None

    def __init__(self, obj):
        self.button = obj

    def Click(self):
        self.button.click()

    def isPresented(self):
        if self.button != None:
            return True
        return False


class LinkClass:
    link = None

    def __init__(self, obj):
        self.link = obj

    def Click(self):
        self.link.click()

    def isPresented(self):
        if self.link != None:
            return True
        return False

    def Address(self):
        return self.link.get_attribute('href')


class EditBoxClass:

    def __init__(self, obj):
        self.edit = obj

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

    def __init__(self, obj):
        self.select = obj

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
    timeout = 300

    def __init__(self, driver):
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(0.01)
        self.driver = driver

    def _find_element(self, parameter):
        obj = None
        k = 0
        while (obj == None and k < self.timeout):
            k += 1
            try:
                obj = self.driver.find_element_by_name(parameter)
                return obj
            except:
                pass
            try:
                obj = self.driver.find_element_by_id(parameter)
                return obj
            except:
                pass
            try:
                obj = self.driver.find_element_by_xpath(parameter)
                return obj
            except:
                pass
            try:
                obj = self.driver.find_element_by_partial_link_text(parameter)
                return obj
            except:
                pass

        return obj

    def Open(self, url):
        self.driver.get(url)

    def Button(self, name):
        obj = self._find_element(name)
        button = ButtonClass(obj)
        return button

    def Link(self, name):
        obj = self._find_element(name)
        link = LinkClass(obj)
        return link

    def EditBox(self, name):
        obj = self._find_element(name)
        edit = EditBoxClass(obj)
        return edit

    def DropDownList(self, name):
        obj = self._find_element(name)
        select = DropDownListClass(obj)
        return select

    def Navigate(self, path):
        steps = path.split(':')

        for step in steps:
            self.Button(step).Click()
