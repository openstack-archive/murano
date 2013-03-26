# -*- coding: utf-8 -*-

import unittest2
from login_page import LoginPage
from datacenters_page import DataCentersPage
from selenium import webdriver

"""
    def test_01_create_data_center(self):
        self.page.create_data_center('dc1')
        assert self.page.Link('dc1').isPresented()

    def test_02_delete_data_center(self):
        self.page.delete_data_center('dc1')
        assert not self.page.Link('dc1').isPresented()

    def test_03_create_data_centers(self):
        for i in range(1, 10):
            name = 'datacenter' + str(i)
            self.page.create_data_center(name)
            assert self.page.Link(name).isPresented()

    def test_04_delete_data_centers(self):
        self.page.delete_data_center('datacenter1')
        self.page.delete_data_center('datacenter9')
        assert not self.page.Link('datacenter1').isPresented()
        assert not self.page.Link('datacenter9').isPresented()

        for i in range(2, 9):
            name = 'datacenter' + str(i)
            assert self.page.Link(name).isPresented()
"""


class SanityTests(unittest2.TestCase):

    @classmethod
    def setUpClass(self):
        driver = webdriver.Firefox()
        self.page = LoginPage(driver)
        self.page.login()
        self.page.Navigate('Project:Windows Data Centers')
        self.page = DataCentersPage(driver)

    @classmethod
    def tearDownClass(self):
        self.page.driver.close()

    def test_05_create_service_ad(self):
        name = 'dc001.local'
        self.page.Navigate('Windows Data Centers')
        self.page.create_data_center('test05')
        self.page = self.page.select_data_center('test05')

        ad_parameters = {'1-dc_name': name,
                         '1-dc_count': 1,
                         '1-adm_password': 'AkvareL707!',
                         '1-recovery_password': 'AkvareL707!'}
        self.page.create_service('Active Directory', ad_parameters)

        assert self.page.Link(name).isPresented()
"""
    def test_06_create_service_ad_two_instances(self):
        name = 'dc002.local'
        self.page.Navigate('Windows Data Centers')
        self.page.create_data_center('test06')
        self.page = self.page.select_data_center('test06')

        ad_parameters = {'1-dc_name': name,
                         '1-dc_count': 2,
                         '1-adm_password': 'P@ssw0rd2',
                         '1-recovery_password': 'P@ssw0rd'}
        self.page.create_service('Active Directory', ad_parameters)

        assert self.page.Link(name).isPresented()

    def test_07_create_service_ad_with_iis(self):
        ad_name = 'dc003.local'
        self.page.Navigate('Windows Data Centers')
        self.page.create_data_center('test07')
        self.page = self.page.select_data_center('test07')

        ad_parameters = {'1-dc_name': ad_name,
                         '1-dc_count': 3,
                         '1-adm_password': 'P@ssw0rd',
                         '1-recovery_password': 'P@ssw0rd2'}
        self.page.create_service('Active Directory', ad_parameters)

        assert self.page.Link(ad_name).isPresented()

        iis_name = 'iis_server1'
        iis_parameters = {'1-iis_name': iis_name,
                          '1-adm_password': 'P@ssw0rd',
                          '1-iis_domain': 'dc003.local',
                          '1-domain_user_name': 'Administrator',
                          '1-domain_user_password': 'P@ssw0rd'}
        self.page.create_service('Internet Information Services',
                                 iis_parameters)

        assert self.page.Link(iis_name).isPresented()

        iis_name = 'iis_server2'
        iis_parameters = {'1-iis_name': iis_name,
                          '1-adm_password': 'P@ssw0rd',
                          '1-iis_domain': 'dc003.local',
                          '1-domain_user_name': 'Administrator',
                          '1-domain_user_password': 'P@ssw0rd'}
        self.page.create_service('Internet Information Services',
                                 iis_parameters)

        assert self.page.Link(iis_name).isPresented()

        iis_name = 'iis_server3'
        iis_parameters = {'1-iis_name': iis_name,
                          '1-adm_password': 'P@ssw0rd',
                          '1-iis_domain': 'dc003.local',
                          '1-domain_user_name': 'Administrator',
                          '1-domain_user_password': 'P@ssw0rd'}
        self.page.create_service('Internet Information Services',
                                 iis_parameters)

        assert self.page.Link(iis_name).isPresented()

    def test_08_deploy_data_center(self):
        ad_name = 'AD.net'
        self.page.Navigate('Windows Data Centers')
        self.page.create_data_center('test08')
        self.page = self.page.select_data_center('test08')

        ad_parameters = {'1-dc_name': ad_name,
                         '1-dc_count': 2,
                         '1-adm_password': 'P@ssw0rd',
                         '1-recovery_password': 'P@ssw0rd2'}
        self.page.create_service('Active Directory', ad_parameters)

        assert self.page.Link(ad_name).isPresented()

        iis_parameters = {'1-iis_name': 'iis_server',
                          '1-adm_password': 'P@ssw0rd',
                          '1-iis_domain': 'AD.net',
                          '1-domain_user_name': 'Administrator',
                          '1-domain_user_password': 'P@ssw0rd'}
        self.page.create_service('Internet Information Services',
                                 iis_parameters)

        assert self.page.Link('iis_server').isPresented()

        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)
        self.page.deploy_data_center('test08')

        status = self.page.get_datacenter_status('test08')
        assert 'Deploy in progress' in status
"""

if __name__ == '__main__':
    unittest2.main()
