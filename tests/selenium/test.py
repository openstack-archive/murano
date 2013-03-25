# -*- coding: utf-8 -*-

import unittest2
from login_page import LoginPage
from datacenters_page import DataCentersPage
from selenium import webdriver


class SanityTests(unittest2.TestCase):

    def setUp(self):
        driver = webdriver.Firefox()
        self.page = LoginPage(driver)
        self.page.login()
        self.page.Navigate('Project:Windows Data Centers')
        self.page = DataCentersPage(driver)

    def tearDown(self):
        self.page.driver.close()

    def test_01_create_data_center(self):
        self.page.create_data_center('dc1')
        assert self.page.Link('dc1').isPresented()

    def test_02_delete_data_center(self):
        self.page.delete_data_center('dc1')
        assert not self.page.Link('dc1').isPresented()

    def test_03_create_data_centers(self):
        for i in range(1, 20):
            name = 'datacenter' + str(i)
            self.page.create_data_center(name)
            assert self.page.Link(name).isPresented()

    def test_04_delete_data_centers(self):
        self.page.delete_data_center('datacenter1')
        self.page.delete_data_center('datacenter20')
        assert not self.page.Link('datacenter1').isPresented()
        assert not self.page.Link('datacenter20').isPresented()

        for i in range(2, 19):
            name = 'datacenter' + str(i)
            assert self.page.Link(name).isPresented()

    def test_05_create_service_ad(self):
        name = 'dc001.local'
        self.page.create_data_center('test')
        self.page.select_data_center('test')

        ad_parameters = {'1-dc_name': name,
                         '1-dc_count': 1,
                         '1-adm_password': 'AkvareL707!',
                         '1-recovery_password': 'AkvareL707!'}
        self.page.create_service('Active Directory', ad_parameters)

        assert self.page.Link(name).isPresented()


if __name__ == '__main__':
    unittest2.main()
