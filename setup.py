#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    # 'ka-lite',  # We do not have a way to specify ka-lite OR ka-lite-static
]

test_requirements = [
    'pytest',
]


from setuptools.command.test import test as TestCommand
class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

import kalite_gtk

setup(
    name='ka-lite-gtk',
    version=kalite_gtk.__version__,
    description="User interface for KA Lite (GTK3)",
    long_description=readme + '\n\n' + history,
    author="Foundation for Learning Equality",
    author_email='info@learningequality.org',
    url='https://github.com/learningequality/ka-lite-gtk',
    packages=[
        'kalite_gtk',
    ],
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='ka-lite-gtk, ka lite, ka-lite',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    cmdclass={'test': PyTest},
    tests_require=test_requirements,
    entry_points={
        'gui_scripts': [
            'ka-lite-gtk = kalite_gtk.__main__:main'
        ]
    },
)
