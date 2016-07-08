# Copyright (c) 2015 Mirantis, Inc.
# All Rights Reserved.
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

from oslo_config import cfg

service_available_group = cfg.OptGroup(name="service_available",
                                       title="Available OpenStack Services")

ServiceAvailableGroup = [
    cfg.BoolOpt("murano",
                default=True,
                help="Whether or not murano is expected to be available"),
    cfg.BoolOpt("murano_cfapi",
                default=False,
                help="Whether or not murano-cfapi is expected to be "
                     "unavailable by default"),
    cfg.BoolOpt("glare",
                default=False,
                help="Whether or not glare is expected to be unavailable")
]

application_catalog_group = cfg.OptGroup(name="application_catalog",
                                         title="Application Catalog Options")

service_broker_group = cfg.OptGroup(name="service_broker",
                                         title="Service Broker Options")

ApplicationCatalogGroup = [
    # Application catalog tempest configuration
    cfg.StrOpt("region",
               default="",
               help="The application_catalog region name to use. If empty, "
                    "the value of identity.region is used instead. "
                    "If no such region is found in the service catalog, "
                    "the first found one is used."),

    cfg.StrOpt("catalog_type",
               default="application-catalog",
               help="Catalog type of Application Catalog."),

    cfg.StrOpt("endpoint_type",
               default="publicURL",
               choices=["publicURL", "adminURL", "internalURL"],
               help="The endpoint type for application catalog service."),

    cfg.IntOpt("build_interval",
               default=3,
               help="Time in seconds between application catalog"
                    " availability checks."),

    cfg.IntOpt("build_timeout",
               default=500,
               help="Timeout in seconds to wait for a application catalog"
                    " to become available."),
    cfg.BoolOpt("glare_backend",
                default=False,
                help="Tells tempest about murano glare backend "
                     "configuration.")
]

ServiceBrokerGroup = [
    # Test runs control
    cfg.StrOpt("run_service_broker_tests",
               default=False,
               help="Defines whether run service broker api tests or not"),

    cfg.StrOpt("catalog_type",
               default="service-broker",
               help="Catalog type of Service Broker API"),

    cfg.StrOpt("endpoint_type",
               default="publicURL",
               choices=["publicURL", "adminURL", "internalURL"],
               help="The endpoint type for service broker service"),

    cfg.IntOpt("build_interval",
               default=3,
               help="Time in seconds between service broker"
                    " availability checks."),

    cfg.IntOpt("build_timeout",
               default=500,
               help="Timeout in seconds to wait for a service broker"
                    " to become available.")


]
