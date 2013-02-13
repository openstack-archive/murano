# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
"""Balancer base exception handling."""

import webob.exc as exception


class NotFound(exception.HTTPNotFound):
    message = 'Resource not found.'

    def __init__(self, message=None, **kwargs):
        super(NotFound, self).__init__(message)
        self.kwargs = kwargs


class DeviceNotFound(NotFound):
    message = 'Device not found'


class NoValidDevice(NotFound):
    message = 'Suitable device not found'


class ServiceNotFound(NotFound):
    message = 'LoadBalancer not found'


class DeviceConflict(exception.HTTPConflict):
    message = 'Conflict while device deleting'

    def __init__(self, message=None, **kwargs):
        super(DeviceConflict, self).__init__(message)
        self.kwargs = kwargs
