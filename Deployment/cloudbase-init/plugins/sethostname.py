
from cloudbaseinit.osutils.factory import *
from cloudbaseinit.plugins.base import *
from cloudbaseinit.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class SetHostNamePlugin(BasePlugin):
    def execute(self, service):
        meta_data = service.get_meta_data('openstack')
        if 'name' not in meta_data:
            LOG.debug('Name not found in metadata')
            return False

        osutils = OSUtilsFactory().get_os_utils()

        new_host_name = meta_data['name'].replace('.', '-')
        return osutils.set_host_name(new_host_name)

