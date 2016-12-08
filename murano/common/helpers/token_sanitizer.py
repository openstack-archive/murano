# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six


class TokenSanitizer(object):
    """Helper class for cleaning some object from different passwords/tokens

    Simply searches attribute with `look a like` name as one of
    the token and replace it value with message.
    """
    def __init__(self, tokens=('token', 'pass', 'trustid'),
                 message='*** SANITIZED ***'):
        """Init method of TokenSanitizer

        :param tokens:  iterable with tokens
        :param message: string by which each token going to be replaced
        """
        self._tokens = tokens
        self._message = message

    @property
    def tokens(self):
        """Iterable with tokens that should be sanitized."""
        return self._tokens

    @property
    def message(self):
        """String by which each token going to be replaced."""
        return self._message

    def _contains_token(self, value):
        for token in self.tokens:
            if token in value.lower():
                return True
        return False

    def sanitize(self, obj):
        """Replaces each token found in object by message.

        :param obj: dict, list, tuple, object
        :return: Sanitized object
        """
        if isinstance(obj, dict):
            return dict([self.sanitize(item) for item in obj.items()])
        elif isinstance(obj, list):
            return [self.sanitize(item) for item in obj]
        elif isinstance(obj, tuple):
            k, v = obj
            if self._contains_token(k) and isinstance(v, six.string_types):
                return k, self.message
            return k, self.sanitize(v)
        else:
            return obj
