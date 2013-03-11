# Copyright 2012 OpenMeter LLC.
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

from portasclient.common import base


def _get_opt_path(simple_params=[], **kwargs):
    l = []
    #get simple paramters
    for key in simple_params:
        val = kwargs.get(key)
        if val:
            l.append(key + '=' + val)
    #get metadata query paramters
    metaquery = kwargs.get('metaquery')
    if metaquery:
        l.extend(metaquery.split(':'))

    return '&'.join(l)


class User(base.Resource):
    def __init__(self, manager, info, loaded=False):
        _d = {unicode('user_id'): info}
        super(User, self).__init__(manager, _d, loaded)

    def __repr__(self):
        return "<User %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class UserManager(base.Manager):
    resource_class = User

    def list(self, **kwargs):
        s = kwargs.get('source')
        if s:
            path = '/sources/%s/users' % (s)
        else:
            path = '/users'
        return self._list('/v1%s' % path, 'users')


class Project(base.Resource):
    def __init__(self, manager, info, loaded=False):
        _d = {unicode('project_id'): info}
        super(Project, self).__init__(manager, _d, loaded)

    def __repr__(self):
        return "<Project %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class ProjectManager(base.Manager):
    resource_class = Project

    def list(self, **kwargs):
        s = kwargs.get('source')
        if s:
            path = '/sources/%s/projects' % (kwargs['source'])
        else:
            path = '/projects'

        return self._list('/v1%s' % path, 'projects')


class Resource(base.Resource):
    def __repr__(self):
        return "<Resource %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class ResourceManager(base.Manager):
    resource_class = Resource

    def list(self, **kwargs):
        u = kwargs.get('user_id')
        s = kwargs.get('source')
        p = kwargs.get('project_id')
        opts_path = _get_opt_path(['start_timestamp', 'end_timestamp'],
                                  **kwargs)
        if u:
            path = '/users/%s/resources' % (u)
        elif s:
            path = '/sources/%s/resources' % (s)
        elif p:
            path = '/projects/%s/resources' % (p)
        else:
            path = '/resources'
        if opts_path:
            path = '/v1%s?%s' % (path, opts_path)
        else:
            path = '/v1%s' % (path)
        return self._list(path, 'resources')


class Sample(base.Resource):
    def __init__(self, manager, info, loaded=False):
        smaller = dict((k, v) for (k, v) in info.iteritems()
                       if k not in ('metadata', 'message_signature'))
        super(Sample, self).__init__(manager, smaller, loaded)

    def __repr__(self):
        return "<Sample %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class SampleManager(base.Manager):
    resource_class = Sample

    def list(self, **kwargs):
        c = kwargs['counter_name']
        r = kwargs.get('resource_id')
        u = kwargs.get('user_id')
        p = kwargs.get('project_id')
        s = kwargs.get('source')
        opts_path = _get_opt_path(['start_timestamp', 'end_timestamp'],
                                  **kwargs)
        if r:
            path = '/resources/%s/meters/%s' % (r, c)
        elif u:
            path = '/users/%s/meters/%s' % (u, c)
        elif p:
            path = '/projects/%s/meters/%s' % (p, c)
        elif s:
            path = '/sources/%s/meters/%s' % (s, c)
        else:
            path = '/meters'

        if opts_path:
            path = '/v1%s?%s' % (path, opts_path)
        else:
            path = '/v1%s' % (path)
        return self._list(path, 'events')


class Meter(base.Resource):
    def __repr__(self):
        return "<Meter %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class MeterManager(base.Manager):
    resource_class = Meter

    def list(self, **kwargs):
        r = kwargs.get('resource_id')
        u = kwargs.get('user_id')
        p = kwargs.get('project_id')
        s = kwargs.get('source')
        opts_path = _get_opt_path(**kwargs)
        if u:
            path = '/users/%s/meters' % u
        elif r:
            path = '/resources/%s/meters' % r
        elif p:
            path = '/projects/%s/meters' % p
        elif s:
            path = '/sources/%s/meters' % s
        else:
            path = '/meters'
        if opts_path:
            path = '/v1%s?%s' % (path, opts_path)
        else:
            path = '/v1%s' % (path)
        return self._list(path, 'meters')
