#
# Copyright IBM Corporation 2021
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys

from glob import glob
from setuptools import setup

long_description = '''The CodeFlare-Pipelines library provides facilities for defining and running parallel 
pipelines on top of Ray. The goal of this project is to unify pipeline workflows across multiple platforms 
such as scikit-learn and Apache Spark, while providing nearly optimal scale-out parallelism on pipelined computations.

For the full documentation see
[https://github.com/project-codeflare/codeflare](https://github.com/project-codeflare/codeflare).
'''

here = os.path.abspath(os.path.dirname(__file__))

version_ns = {}
with open(os.path.join(here, 'codeflare', '_version.py')) as f:
    exec(f.read(), {}, version_ns)

setup(
    name='codeflare',
    version=version_ns['__version__'],
    packages=['codeflare', 'codeflare.pipelines', 'codeflare.pipelines.tests'],
    install_requires=[
        'ray[default,serve,k8s]>=1.3.0',
        'setuptools>=52.0.0',
        'sklearn>=0.0',
        'scikit-learn>=0.24.1',
        'pandas>=1.2.4',
        'numpy>=1.18.5',
        'pickle5>=0.0.11', 
        'graphviz>=0.16',
    ],
    url='https://github.com/project-codeflare/codeflare',
    license='Apache v2.0',
    author='CodeFlare team',
    author_email='chcost@us.ibm.com',
    description='Codeflare pipelines',
    python_requires='>=3.8',
    keywords=("ray pipelines"),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: OS Independent',
        'Topic :: System :: Distributed Computing',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/project-codeflare/codeflare/issues',
        'Source': 'https://github.com/project-codeflare/codeflare',
    },
)