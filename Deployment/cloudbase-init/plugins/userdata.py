# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Cloudbase Solutions Srl
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re
import tempfile
import uuid
import email
import tempfile
import os
import errno

from cloudbaseinit.openstack.common import cfg
from cloudbaseinit.openstack.common import log as logging
from cloudbaseinit.osutils.factory import *
from cloudbaseinit.plugins.base import *

LOG = logging.getLogger(__name__)

opts = [
    cfg.StrOpt('user_data_folder', default='cloud-data',
        help='Specifies a folder to store multipart data files.'),
    ]

CONF = cfg.CONF
CONF.register_opts(opts)

class UserDataPlugin():
    def __init__(self, cfg=CONF):
        self.cfg = cfg
        self.msg = None
        return

    def execute(self, service):
        user_data = service.get_user_data('openstack')
        if not user_data:
            return False

        LOG.debug('User data content:\n%s' % user_data)

        if user_data.startswith('Content-Type: multipart'):
            for part in self.parse_MIME(user_data):
                self.process_part(part)
        else:
            self.handle(user_data)
        return

    def process_part(self, part):
        if part.get_filename() == 'cfn-userdata':
            self.handle(part.get_payload())
        return

    def parse_MIME(self, user_data):
        folder = self.cfg.user_data_folder
        self.create_folder(folder)

        self.msg = email.message_from_string(user_data)
        return self.msg.walk()


    def create_folder(self, folder):
        try:
            os.mkdir(folder)
        except os.OSError, e:
            if e.errno != errno.EEXIST:
                raise e
        return

    def handle(self, user_data):

        osutils = OSUtilsFactory().get_os_utils()

        target_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        if re.search(r'^rem cmd\s', user_data, re.I):
            target_path += '.cmd'
            args = [target_path]
            shell = True
        elif re.search(r'^#!', user_data, re.I):
            target_path += '.sh'
            args = ['bash.exe', target_path]
            shell = False
        elif re.search(r'^#ps1\s', user_data, re.I):
            target_path += '.ps1'
            args = ['powershell.exe', '-ExecutionPolicy', 'RemoteSigned',
                    '-NonInteractive', target_path]
            shell = False
        else:
            # Unsupported
            LOG.warning('Unsupported user_data format')
            return False

        try:
            with open(target_path, 'wb') as f:
                f.write(user_data)
            (out, err, ret_val) = osutils.execute_process(args, shell)

            LOG.info('User_data script ended with return code: %d' % ret_val)
            LOG.debug('User_data stdout:\n%s' % out)
            LOG.debug('User_data stderr:\n%s' % err)
        except Exception, ex:
            LOG.warning('An error occurred during user_data execution: \'%s\'' % ex)
        finally:
            if os.path.exists(target_path):
                os.remove(target_path)

        return False

