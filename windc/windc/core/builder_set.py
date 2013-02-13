# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

from builder import Builder

import imp
import os
import sys, glob
import logging
import traceback

LOG = logging.getLogger(__name__)
global builders

def load_from_file(filepath):
    class_inst = None

    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])

    if file_ext.lower() == '.py':
        py_mod = imp.load_source(mod_name, filepath)

    elif file_ext.lower() == '.pyc':
        py_mod = imp.load_compiled(mod_name, filepath)

    if hasattr(py_mod, mod_name):
    	callable = getattr(__import__(mod_name),mod_name)
        class_inst = callable()

    return class_inst


class BuilderSet:
	def __init__(self):
		self.path = './windc/core/builders'
		sys.path.append(self.path)
		self.set = {}

	def load(self):

		files = glob.glob(self.path+'/*.py')

		for file in files:
			LOG.debug("Trying to load builder from file: %s", file)
			try:
				builder = load_from_file(file)
				LOG.info("Buider '%s' loaded.", builder.name)
				self.set[builder.type] = builder
			except:
				exc_type, exc_value, exc_traceback = sys.exc_info()
				LOG.error('Can`t load builder from the file %s. Skip it.', file)
				LOG.debug(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)))


	def reload(self):
		self.set = {}
		self.load()
