__author__ = 'katharine'

from setuptools import setup, find_packages

setup(name='libpebble2',
      version='0.0.0',
      description='Library for communicating with pebbles over pebble protocol',
      url='https://github.com/pebble/kb-libpebble2',
      author='Pebble Technology Corporation',
      author_email='katharine@pebble.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
        'enum34>=1.0.4',
        'websocket-client>=0.31.0',
      ],
      zip_safe=True)