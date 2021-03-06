# Copyright 2017, OpenCensus Authors
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

"""A setup module for Open Source Census Instrumentation Library"""

import io
from setuptools import setup, find_packages

extras = {}

install_requires = [
    "aiotask-context==0.5.0",
    "opencensus==0.5.0",
    "thrift==0.10.0",
    "libhoney==1.7.1",
]

packages = [
    package for package in find_packages()
    if package.startswith('qubit')]

namespaces = ['qubit']

setup(
    name='qubit-opencensus',
    version='0.5.0',
    author='Qubit',
    author_email='tristan@qubit.com',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    description='Various extensions for OpenCensus',
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=install_requires,
    extras_require=extras,
    license='Apache-2.0',
    packages=packages,
    namespace_packages=namespaces,
    url='https://github.com/TauntNow/opencensus-utils')
