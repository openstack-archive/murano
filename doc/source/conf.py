#    Copyright (C) 2014 Mirantis Inc
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

import os
import subprocess
import sys
import warnings

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('../../'))
sys.path.insert(0, os.path.abspath('../'))
sys.path.insert(0, os.path.abspath('./'))

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.doctest',
              'sphinx.ext.todo',
              'sphinx.ext.coverage',
              'oslo_config.sphinxconfiggen',
              'oslo_config.sphinxext',
              'oslo_policy.sphinxext',
              'oslo_policy.sphinxpolicygen',
              'sphinx.ext.viewcode',
              'sphinxcontrib.httpdomain',]

if not on_rtd:
    extensions.append('openstackdocstheme')

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Murano'

# openstackdocstheme options
repository_name = 'openstack/murano'
bug_project = 'murano'
bug_tag = ''
html_last_updated_fmt = '%Y-%m-%d %H:%M'

config_generator_config_file = '../../etc/oslo-config-generator/murano.conf'
sample_config_basename = '_static/murano'

policy_generator_config_file = [
    ('../../etc/oslo-policy-generator/murano-policy-generator.conf',
     '_static/murano'),
]

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
from murano.version import version_info
release = version_info.release_string()
version = version_info.version_string()

# Set the default Pygments syntax
highlight_language = 'python'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['specification/murano-repository.rst',
                    'specification/murano-api.rst',
                    'murano_pl/builtin_functions.rst',
                    'install/configure_network.rst',
                    'articles/ad-ui.rst',
                    'articles/telnet.rst']

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
show_authors = False

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

if not on_rtd:
    #TODO(efedorova): Change local theme to correspond with the theme on rtd
    pass

# The name for this set of Sphinx documents. If None, it defaults to
# "<project> v<release> documentation".
html_title = 'Murano'
html_theme = 'openstackdocs'

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    'index':    ['sidebarlinks.html', 'localtoc.html', 'searchbox.html', 'sourcelink.html'],
    '**':       ['localtoc.html', 'relations.html',
                 'searchbox.html', 'sourcelink.html']
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
