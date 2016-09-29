#    Copyright (c) 2013 Mirantis, Inc.
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

ENV_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",

    "type": "object",
    "properties": {
        "?": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "_actions": {"type": "object"}
            },
            "required": ["id", "type"]
        },
        "name": {"type": "string"},
        "region": {"type": ["string", "null"]},
        "regions": {"type": "object"},
        "defaultNetworks": {
            "type": "object",
            "properties": {
                "environment": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "?": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "id": {"type": "string"},
                                "name": {"type": "string"}
                            },
                        },
                        "autoUplink": {"type": "boolean"},
                        "externalRouterId": {"type": "string"},
                        "dnsNameServers": {"type": "array"},
                        "autogenerateSubnet": {"type": "boolean"},
                        "subnetCidr": {"type": "string"},
                        "openstackId": {"type": "string"},
                        "regionName": {"type": "string"}
                    },
                    "required": ["name", "?"]
                },
                "flat": {"type": ["boolean", "null"]}
            },
            "required": ["environment", "flat"]
        },
        "services": {
            "type": "array",
            "minItems": 0,
            "items": {"type": "object"}
        }
    },
    "required": ["?", "name", "region", "defaultNetworks"]
}

PKG_UPLOAD_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",

    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "minItems": 0,
            "items": {"type": "string"},
            "uniqueItems": True
        },
        "categories": {
            "type": "array",
            "minItems": 0,
            "items": {"type": "string"},
            "uniqueItems": True
        },
        "description": {"type": "string"},
        "name": {"type": "string"},
        "is_public": {"type": "boolean"},
        "enabled": {"type": "boolean"}
    },
    "additionalProperties": False
}

PKG_UPDATE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",

    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True
        },
        "categories": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True
        },
        "description": {"type": "string"},
        "name": {"type": "string"},
        "is_public": {"type": "boolean"},
        "enabled": {"type": "boolean"}
    },
    "additionalProperties": False,
    "minProperties": 1,
}
