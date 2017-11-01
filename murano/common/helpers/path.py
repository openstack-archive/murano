# Copyright (c) 2017 Mirantis Inc.
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

import os.path


def secure_join(*parts):
    """Secure version of os.path.join(*parts)

    Joins pathname components and ensures that with each join the result
    is a subdirectory of the previous join
    """
    new = prev = ""
    for part in parts:
        new = os.path.normpath(os.path.join(prev, part))
        if len(new) <= len(prev) or prev != "" and not new.startswith(
                prev + os.path.sep):
            raise ValueError('path {0} is not allowed {1}'.format(
                os.path.join(*parts), parts))
        prev = new
    return new
