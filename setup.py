#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='nakagawa',
      version="0.4",
      description='Nakagawa - central river',
      author='bigretromike',
      url='https://github.com/bigretromike/nakagawa/',
      packages=["nakagawa", ],
      install_requires=[
          'sqlalchemy>=1.1.9',
          'wallabag_api>=1.1.0',
          'BASC-py4chan>=0.6.3',
          'logging>=0.4.9.6'
      ],
      license='MIT'
      )
