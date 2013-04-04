import logging


logging.basicConfig()
LOG = logging.getLogger(' Test Case: ')


class TestCase:
    name = None
    driver = None

    def __init__(self, driver, name):
        self.name = name
        self.driver = driver

    def verify(self, condition):
        try:
            self.driver.save_screenshot(self.name)
        except:
            LOG.critical("Can not create screenshot file.")
        if condition:
            LOG.info(self.name + "  PASSED")
            return True
        else:
            LOG.critical(self.name + "  FAILED")
            return False