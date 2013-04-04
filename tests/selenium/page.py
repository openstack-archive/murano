import logging
from selenium.webdriver.support.ui import Select
import xml.etree.ElementTree as ET


logging.basicConfig()
LOG = logging.getLogger(' Page object: ')
"""
    Disable selenium logging:
"""
logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
logger.setLevel('ERROR')


class ObjectsLibrary:
    file = None
    objects = []

    def __init__(self, file_name='objects.xml'):
        """
            Initialization of the Objects Library.
            Read objects descriptions from XML file.
        """
        self.file = file_name
        tree = ET.parse(self.file)
        objects = tree.getroot()
        self.objects = []
        for element in objects:
            object = {}
            for parameter in element:
                object.update({parameter.tag: parameter.text})
            self.objects.append(object)

    def get_object(self, name, pagename):
        """
            Search objects in Objects Library.
        """
        for object in self.objects:
            obj_pagename = object.get('pagename', None)
            if object['name'] == name and (obj_pagename == pagename
                                           or obj_pagename is None):
                return object['parameter']
        return None


class TableCellClass:
    table = None

    def __init__(self, obj):
        if not obj:
            LOG.error('TableCell does not found')
        self.table = obj

    def Text(self):
        if self.table:
            LOG.critical(self.table.text)
            return self.table.text
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
            try:
                self.edit.clear()
                self.edit.send_keys(value)
            except:
                LOG.error('Can not set value for text box.')

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
            try:
                Select(self.select).select_by_visible_text(value)
            except:
                LOG.error('Can not select element %s from drop down list.'
                          .format(value))

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
    timeout = 10
    lib = None
    name = None

    def __init__(self, driver):
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(0.01)
        self.driver = driver

    def _find_element(self, name, parameter=None):
        """
            This method allows to find element,
            based on descriptions in Object Library,
            xpath, id, name or pertial link text.
            If parameter != None will be used name % parameter
        """
        lib = ObjectsLibrary()
        if lib.get_object(name, self.name):
            name = lib.get_object(name, self.name)

        if parameter:
            name = name % parameter

        obj = None
        k = 0

        while (obj is None and k < self.timeout):
            k += 1

            try:
                obj = self.driver.find_element_by_name(name)
                return obj
            except:
                pass
            try:
                obj = self.driver.find_element_by_id(name)
                return obj
            except:
                pass
            try:
                obj = self.driver.find_element_by_xpath(name)
                return obj
            except:
                pass
            try:
                obj = self.driver.find_element_by_partial_link_text(name)
                return obj
            except:
                pass

        LOG.error(error_msg % name)
        return None

    def Open(self, url):
        self.driver.get(url)

    def Refresh(self):
        self.driver.refresh()

    def TableCell(self, name, parameter=None):
        obj = self._find_element(name, parameter)
        table = TableCellClass(obj)
        return table

    def Button(self, name, parameter=None):
        obj = self._find_element(name, parameter)
        button = ButtonClass(obj)
        return button

    def Link(self, name, parameter=None):
        obj = self._find_element(name, parameter)
        link = LinkClass(obj)
        return link

    def EditBox(self, name, parameter=None):
        obj = self._find_element(name, parameter)
        edit = EditBoxClass(obj)
        return edit

    def DropDownList(self, name, parameter=None):
        obj = self._find_element(name, parameter)
        select = DropDownListClass(obj)
        return select

    def Navigate(self, path):
        """
            This method allows to navigate by
            webUI menu button and links to
            the specific page
        """
        steps = path.split(':')

        for step in steps:
            self.Button(step).Click()
