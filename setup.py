from distutils.core import setup
import pkg_resources  # part of setuptools
version = pkg_resources.require("ris")[0].version

setup(name='ris',
      version=version,
      packages=['ris']
      )
