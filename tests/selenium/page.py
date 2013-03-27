import logging
from selenium.webdriver.support.ui import Select
logging.basicConfig()
LOG = logging.getLogger(' Page object: ')


class TableCellClass:
    table = None

    def __init__(self, obj):
        if not obj:
            LOG.error('TableCell does not found')
        self.table = obj

    def Text(self):
        if self.table:
            return self.table.text()
        else:
            return ''


class ButtonClass:
    button = None

    def __init__(self, obj):
        if not obj:
            LOG.error('Button does not found')
        self.button = obj

    def Click(self):
        if self.button:
            self.button.click()

    def isPresented(self):
        if self.button:
            return True
        return False


class LinkClass:
    link = None

    def __init__(self, obj):
        if not obj:
            LOG.error('Link does not found')
        self.link = obj

    def Click(self):
        if self.link:
            self.link.click()

    def isPresented(self):
        if self.link:
            return True
        return False

    def Address(self):
        if self.link:
            return self.link.get_attribute('href')
        else:
            return ''


class EditBoxClass:

    def __init__(self, obj):
        if not obj:
            LOG.error('EditBox does not found')
        self.edit = obj

    def isPresented(self):
        if self.edit:
            return True
        return False

    def Set(self, value):
        if self.edit:
            self.edit.clear()
            self.edit.send_keys(value)

    def Text(self):
        if self.edit:
            return self.edit.get_text()
        else:
            return ''


class DropDownListClass:
    select = None

    def __init__(self, obj):
        if not obj:
            LOG.error('DropDownList does not found')
        self.select = obj

    def isPresented(self):
        if self.select is not None:
            return True
        return False

    def Set(self, value):
        if self.select:
            Select(self.select).select_by_visible_text(value)

    def Text(self):
        if self.select:
            return self.select.get_text()
        else:
            return ''


error_msg = """
                Object with parameter: %s
                does not found on page.
            """


class Page:

    driver = None
    timeout = 30

    def __init__(self, driver):
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(0.01)
        self.driver = driver

    def _find_element(self, parameter):
        obj = None
        k = 0
        while (obj is None and k < self.timeout):
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

        LOG.error(error_msg % parameter)
        return None

    def Open(self, url):
        self.driver.get(url)

    def Refresh(self):
        self.driver.refresh()

    def TableCell(self, name):
        obj = self._find_element(name)
        table = TableCellClass(obj)
        return table

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
