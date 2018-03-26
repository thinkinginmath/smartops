"""setup script."""
try:
    from setuptools import find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()


from setuptools.command.test import test as TestCommand
from setuptools import setup


import os
import sys


# This helps python setup.py test command to utilize tox
# See the instruction at https://testrun.org/tox/latest/example/basic.html\
#                 #integration-with-setuptools-distribute-test-commands

class Tox(TestCommand):
    """Tox to do the setup."""

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


INSTALL_REQUIRES_FILE = os.path.join(
    os.path.dirname(__file__), 'requirements.txt')
with open(INSTALL_REQUIRES_FILE, 'r') as requires_file:
    REQUIREMENTS = [line.strip() for line in requires_file if line != '\n']

"""
DATA_FILES_DIR = os.path.join(
    os.path.dirname(__file__), 'conf')
DATA_FILES = []
for parent_dir, sub_dirs, files in os.walk(DATA_FILES_DIR):
    if files == []:
        pass
    for file in files:
        DATA_FILES.append((parent_dir, [os.path.join(parent_dir, file)]))
"""

setup(
    name='smartops',
    version='0.1.0',

    # general info
    description="""SmartOps: Smart APM with
                    Capacity Planning and Remediation""",
    author='SmartOps Development Group',
    author_email='xicheng.chang1@huawei.com',
    url='',
    download_url='',

    # dependency
    #install_requires=REQUIREMENTS,
    packages=find_packages(exclude=['']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    # data
    # data_files=DATA_FILES,
    # test,
    tests_require=['tox'],
    cmdclass={'test': Tox},
)
