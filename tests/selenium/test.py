# -*- coding: utf-8 -*-

import unittest2
import logging
from login_page import LoginPage
from datacenters_page import DataCentersPage
from test_case import TestCase
from selenium import webdriver


logging.basicConfig()
LOG = logging.getLogger(' Tests: ')


def generate_ad(name="test", count=1):
    """
        This function generates parameters for
        Active Directory service
    """
    ad_parameters = {'1-dc_name': name,
                     '1-dc_count': count,
                     '1-adm_password': "P@ssw0rd",
                     '1-recovery_password': "P@ssw0rd2"}
    return ['Active Directory', ad_parameters]

def generate_iis(name="test", domain="test"):
    """
        This function generates parameters for
        Internet Information Services service
    """
    iis_parameters = {'1-iis_name': name,
                      '1-adm_password': "P@ssw0rd",
                      '1-iis_domain': domain}
    return ['Internet Information Services', iis_parameters]


class SanityTests(unittest2.TestCase):

    @classmethod
    def setUpClass(self):
        """
            Open browser, navigate to the login page,
            login and navigate to the Windows Data Centers page
        """
        driver = webdriver.Firefox()
        self.page = LoginPage(driver)
        self.page.login()
        self.page.Navigate('Project:Windows Data Centers')
        self.page = DataCentersPage(driver)

    @classmethod
    def tearDownClass(self):
        """
            Close browser
        """
        self.page.driver.close()

    def test_001_create_data_center(self):
        self.page.create_data_center('dc1')
        assert self.page.Link('dc1').isPresented()

    def test_002_delete_data_center(self):
        self.page.delete_data_center('dc1')
        assert not self.page.Link('dc1').isPresented()

    def test_003_deploy_data_center(self):
        ad_name = "AD.net"
        iis_name = "iis_server"
        self.page.Navigate('Windows Data Centers')
        self.page.create_data_center('data_center_for_deploy')
        self.page = self.page.select_data_center('data_center_for_deploy')

        self.page.create_service(generate_ad(ad_name, 2))
        assert self.page.Link(ad_name).isPresented()

        self.page.create_service(generate_iis(iis_name, ad_name))
        assert self.page.Link(iis_name).isPresented()

        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)
        self.page.deploy_data_center('data_center_for_deploy')

        status = self.page.get_datacenter_status('data_center_for_deploy')
        assert 'Deploy in progress' in status

    def test_004_create_data_centers(self):
        for i in range(1, 10):
            name = "datacenter" + str(i)
            self.page.create_data_center(name)
            assert self.page.Link(name).isPresented()

    def test_005_delete_data_centers(self):
        self.page.delete_data_center('datacenter1')
        self.page.delete_data_center('datacenter9')
        assert not self.page.Link('datacenter1').isPresented()
        assert not self.page.Link('datacenter9').isPresented()

        for i in range(2, 9):
            name = 'datacenter' + str(i)
            assert self.page.Link(name).isPresented()

    def test_006_create_service_ad(self):
        name = "dc001.local"
        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)

        self.page.create_data_center('test05')
        self.page = self.page.select_data_center('test05')

        self.page.create_service(generate_ad(name, 1))

        test_case = TestCase(self.page.driver, test_name)
        assert test_case.verify(self.page.Link(name).isPresented())

    def test_007_create_service_ad_two_instances(self):
        test_name = "Create AD service with two instances"
        name = "dc002.local"
        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)

        self.page.create_data_center('test06')
        self.page = self.page.select_data_center('test06')

        self.page.create_service(generate_ad(name, 2))

        test_case = TestCase(self.page.driver, test_name)
        assert test_case.verify(self.page.Link(name).isPresented())

    def test_008_create_service_ad_with_iis(self):
        test_name = "Create data center with a few services"
        ad_name = "dc003.local"
        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)

        self.page.create_data_center('test07')
        self.page = self.page.select_data_center('test07')

        self.page.create_service(generate_ad(ad_name, 3))

        test_case = TestCase(self.page.driver, test_name)
        assert test_case.verify(self.page.Link(ad_name).isPresented())

        for i in range(5):
            iis_name = 'iis_server' + str(i)
            self.page.create_service(generate_iis(iis_name, ad_name))
            assert test_case.verify(self.page.Link(iis_name).isPresented())

    def test_009_delete_data_center_with_services(self):
        test_name = "Delete data center with a few services with status ready to deploy"
        dc_name = "test07"

        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)
        self.page.delete_data_center(dc_name)

        test_case = TestCase(self.page.driver, test_name)
        assert test_case.verify(not self.page.Link(dc_name).isPresented())

    def test_010_service_deploy_in_progress_status(self):
        test_name = "Check status for services in deploing state"
        
        dc_name = "data_center_for_deploy"
        ad_name = "AD.net"
        iis_name = "iis_server"

        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)
        self.page = self.page.select_data_center(dc_name)
        
        ad_status = self.page.get_service_status(ad_name)
        iis_status = self.page.get_service_status(iis_name)

        test_case = TestCase(self.page.driver, test_name)
        assert test_case.verify('Deploy in progress' in ad_status)
        assert test_case.verify('Deploy in progress' in iis_status)

    def test_011_show_service_details_for_deploy(self):
        test_name = "Check IIS service details page"
        dc_name = "data_center_for_deploy"
        ad_name = "AD.net"
        iis_name = "iis_server"

        self.page.Navigate('Windows Data Centers')
        self.page = DataCentersPage(self.page.driver)
        self.page = self.page.select_data_center(dc_name)
        self.page = self.page.select_service(iis_name)

        name = self.page.get_service_name()
        domain = self.page.get_service_domain()

        test_case = TestCase(self.page.driver, test_name)
        assert test_case.verify(name == iis_name)
        assert test_case.verify(name == ad_name)


if __name__ == '__main__':
    unittest2.main()
