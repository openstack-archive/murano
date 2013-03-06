import codecs

from cloudbaseinit.osutils.factory import *
from cloudbaseinit.plugins.base import *
from cloudbaseinit.openstack.common import log as logging

opts = [
    cfg.StrOpt('agent_config_file', default='C:\\Keero\\Agent\\WindowsAgent.exe.config', help='')
]

CONF = cfg.CONF
CONF.register_opts(opts)

LOG = logging.getLogger(__name__)


class SetHostNamePlugin(BasePlugin):
    def execute(self, service):
        meta_data = service.get_meta_data('openstack')
        if 'meta' not in meta_data:
            LOG.debug("Section 'meta' not found in metadata")
            return False

        if 'agent_config_xml' not in meta_data['meta']:
        	LOG.debug("Config for agent not found in metadata section")
        	return False

        try:
	        configFile=codecs.open(CONF.agent_config_file, encoding='utf-8', mode='w+')
	        configFile.write(meta_data['meta']['agent_config_xml'])
	        configFile.close()
	    except:
	    	LOG.error("Unable to update agent file.")
	    	return False

	    return True

