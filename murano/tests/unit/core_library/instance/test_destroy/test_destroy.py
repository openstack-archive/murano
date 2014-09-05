# Copyright (c) 2014 Mirantis, Inc.
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

from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


TEMPLATE = {
    "outputs": {
        "instance64464-assigned-ip": {
            "value": {"get_attr": ["instance64464", "addresses"]}
        },
        "instance64464-FloatingIPaddress": {
            "value": {"get_attr": ["instance64464", "addresses"]}
        }
    },
    "resources": {
        "instance64464": {
            "type": "OS::Nova::Server",
            "properties": {
                "key_name": None,
                "flavor": "m1.medium",
                "image": "cloud-fedora-v3",
            }
        }
    }
}


class TestDestroy(test_case.DslTestCase):
    def test_destroy_removes_ip_address_from_outputs(self):
        # FIXME(sergmelikyan): Revise this as part of proper fix for #1359998
        self.skipTest('skipped until proper fix for #1359998 is proposed')

        heat_stack_obj = om.Object('io.murano.system.HeatStack')
        instance_obj = om.Object(
            'io.murano.resources.Instance',
            name='instance64464',
            flavor='m1.medium',
            image='cloud-fedora-v3'
        )

        runner = self.new_runner({
            'Objects': om.Object(
                'io.murano.Environment',
                stack=heat_stack_obj,
                instance=instance_obj
            ),
            'Attributes': [
                om.Attribute(heat_stack_obj, 'stack', TEMPLATE),
                om.Attribute(instance_obj, 'fipAssigned', True)
            ]
        })

        empty_env = runner.serialized_model
        empty_env['Objects']['instance'] = None
        model = self.new_runner(empty_env).serialized_model
        template = self.find_attribute(
            model, heat_stack_obj.id, heat_stack_obj.type_name, 'stack'
        )

        instance_name = 'instance64464'
        ip_addresses = '{0}-assigned-ip'.format(instance_name)
        floating_ip = '{0}-FloatingIPaddress'.format(instance_name)

        self.assertNotIn(ip_addresses, template['outputs'])
        self.assertNotIn(floating_ip, template['outputs'])
        self.assertNotIn(instance_name, template['resources'])
