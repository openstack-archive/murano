# -*- coding: utf-8 -*-


import unittest2
import requests
import json
import logging
import thread
import time

logging.basicConfig()
LOG = logging.getLogger(' REST service tests')

class TestSuite(unittest2.TestCase):
    
    def setUp(self):
        self.max_count = 200
        self.url = 'http://localhost:8082/environments'
        self.headers = {'X-Auth-Token': '3685674500ff83eb62b5c5d453e0cacd'}
        self.lock_list = []
        self.responses = []
        self.state = 'stop'

    def tearDown(self):
        self.headers = {}
    
    def run_in_parrallel(self, func, parameter):
        lock = thread.allocate_lock()
        lock.acquire()
        self.lock_list.append(lock)
        thread.start_new_thread(func, (parameter, lock))
        
    def wait_threads(self):
        self.state = 'run'
        while(any([l.locked() for l in self.lock_list])):
            pass
        
        LOG.critical(self.lock_list)

    def create_environment(self, name, lock):
        while (self.state == 'stop'):
            pass
        
        body = '{"name": "%s"}' % name
        response = requests.request('POST',
                                    self.url,
                                    headers=self.headers,
                                    data=body)
        
        self.responses.append(response)

        return lock.release()

        
    def delete_environment(self, id, lock):
        while (self.state == 'stop'):
            pass

        id = '/' + id

        response = requests.request('DELETE', self.url+id, headers=self.headers)

        self.responses.append(response)

        return lock.release()

    def test_01_delete_environments(self):

        response = requests.request('GET', self.url, headers=self.headers)

        result = json.loads(response._content)
        environments = result['environments']

        for env in environments:
            self.run_in_parrallel(self.delete_environment, env['id'])

        self.wait_threads()
        
        for response in self.responses:
            assert response.status_code is 200

    def test_02_list_environments(self):
        
        response = requests.request('GET', self.url, headers=self.headers)
        
        result = json.loads(response._content)
        environments = result['environments']
        
        assert len(environments) is 0
        
    def test_03_create_environment(self):
        
        self.headers.update({'Content-Type': 'application/json'})
        body = '{"name": "test"}'
        
        response = requests.request('POST', self.url, headers=self.headers,
                                    data=body)
        
        environment = json.loads(response._content)
        
        assert environment['name'] == 'test'
    
    def test_04_delete_environment(self):

        id = None

        response = requests.request('GET', self.url, headers=self.headers)

        result = json.loads(response._content)
        environments = result['environments']

        for env in environments:
            if env['name'] == 'test':
                id = '/' + env['id']

        assert id is not None

        response = requests.request('DELETE', self.url+id, headers=self.headers)

        assert response.status_code is 200

    def test_05_create_environments(self):

        self.headers.update({'Content-Type': 'application/json'})

        for i in range(self.max_count):
            name = "environment%s" % i
            self.run_in_parrallel(self.create_environment, name)

        self.wait_threads()
        
        for response in self.responses:
            assert response.status_code is 200            
            
    def test_06_list_environments(self):

        response = requests.request('GET', self.url, headers=self.headers)

        result = json.loads(response._content)
        environments = result['environments']

        assert len(environments) == self.max_count


    def test_07_list_environments(self):

        response = requests.request('GET', self.url, headers=self.headers)

        result = json.loads(response._content)
        environments = result['environments']

        assert len(environments) > 0

    def test_08_list_environments(self):

        response = requests.request('GET', self.url, headers=self.headers)

        result = json.loads(response._content)
        environments = result['environments']

        for env in environments:
            assert env.get('id', None) is not None
            assert env.get('name', None) is not None
            assert env.get('status', None) is not None
            assert env.get('updated', None) is not None
            assert env.get('created', None) is not None
            assert env.get('tenant_id', None) is not None



if __name__ == '__main__':
    unittest2.main()