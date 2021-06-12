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

from setuptools import setup

long_description = '''The CodeFlare-Pipelines library provides facilities for defining and running parallel 
pipelines on top of Ray. The goal of this project is to unify pipeline workflows across multiple platforms 
such as scikit-learn and Apache Spark, while providing nearly optimal scale-out parallelism on pipelined computations.

For the full documentation see
[https://github.ibm.com/codeflare/ray-pipeline](https://github.ibm.com/codeflare/ray-pipeline).
'''

setup(
    name='codeflare-pipelines',
    version='1.0.0',
    packages=['codeflare', 'codeflare.pipelines'],
    install_requires=[
        'ray[default,serve,k8s]>=1.3.0'
    ],
    url='https://github.ibm.com/project-codeflare',
    license='Apache v2.0',
    author='Raghu Ganti, Mudhakar Srivatsa',
    author_email='rganti@us.ibm.com',
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
        'Bug Reports': 'https://github.ibm.com/codeflare/ray-pipeline/issues',
        'Source': 'https://github.ibm.com/codeflare/ray-pipeline',
    },
)