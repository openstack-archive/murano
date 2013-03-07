import untitests
from datacenters_page import DataCentersPage


class SanityTests():

    def setUp(self):
        self.page = DataCentersPage()

    def tearDown(self):
        self.page.close()

    def test_01_create_data_center(self):
        self.page.create_data_center('dc1')
        assert self.page.find_data_center('dc1') is not None

    def test_02_delete_data_center(self):
        self.page.delete_data_center('dc1')
        assert self.page.find_data_center('dc1') is None

    def test_03_create_data_centers(self):
        for i in range(1, 20):
            name = 'datacenter' + str(i)
            self.page.create_data_center(name)
            assert self.page.find_data_center(name) is not None

    def test_04_delete_data_centers(self):
        self.page.delete_data_center('datacenter1')
        self.page.delete_data_center('datacenter20')
        assert self.page.find_data_center('datacenter1') is None
        assert self.page.find_data_center('datacenter20') is None

        for i in range(2, 19):
            name = 'datacenter' + str(i)
            assert self.page.find_data_center(name) is not None

    def test_05_create_service_ad(self):
        name = 'dc001.local'
        self.page.create_data_center(name)
        self.select_data_center(name)
        
        ad_parameters = {'1-dc_name': name,
                         '1-dc_count': 1,
                         '1-adm_password': 'AkvareL707!',
                         '1-recovery_password': 'AkvareL707!'}
        self.page.create_service('Active Directory', ad_parameters)
        
        assert self.page.find_service(name) is not None