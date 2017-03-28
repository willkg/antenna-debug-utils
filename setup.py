# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from setuptools import setup, find_packages
import re
import os


READMEFILE = 'README.rst'
VERSIONFILE = os.path.join('antenna_debug_utils', '__init__.py')
VSRE = r"""^__version__ = ['"]([^'"]*)['"]"""


def get_version():
    version_file = open(VERSIONFILE, 'rt').read()
    return re.search(VSRE, version_file, re.M).group(1)


setup(
    name='antenna-debug-utils',
    version=get_version(),
    description='Scripts for debugging Antenna and infrastructure',
    long_description=open(READMEFILE).read(),
    license="MPLv2",
    author='Will Kahn-Greene',
    author_email='willkg@mozilla.com',
    keywords='antenna socorro crashcollector breakpad',
    url='http://github.com/willkg/antenna-debug-utils',
    zip_safe=True,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points="""
        [console_scripts]
        faux-processor=antenna_debug_utils.faux_processor:cli_main
        log-parser=antenna_debug_utils.log_parser:main
        verify-crashids=antenna_debug_utils.verify_crashids:main
    """,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)
