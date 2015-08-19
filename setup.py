from setuptools import setup
import sys

setup(name='benchmarktool',
      version='0.0.1',
      description='Benchmark tool for hosts',
      url='http://github.com/nuodb/TBD',
      author='Rich Kourtz',
      author_email='info@nuodb.com',
      data_files=[('data', ['data/google-credentials.json'])],
      install_requires=["gspread", "oauth2client", "PyCrypto"], 
      license='BSD licence, see LICENSE',
      #packages=['nuodbawsquickstart'],
      scripts=["bin/benchmark.py"],
      zip_safe=True)
