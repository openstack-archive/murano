# Copyright (c) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import zipfile


class ZipUtilsMixin(object):
    @staticmethod
    def zip_dir(parent_dir, dir):
        abs_path = os.path.join(parent_dir, dir)
        path_len = len(abs_path) + 1
        zip_file = abs_path + ".zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            for dir_name, _, files in os.walk(abs_path):
                for filename in files:
                    fn = os.path.join(dir_name, filename)
                    zf.write(fn, fn[path_len:])
        return zip_file
