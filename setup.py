from distutils.core import setup
# import pkg_resources  # part of setuptools
# version = pkg_resources.require("ris")[0].version

setup(name='ris',
      version='1.3',
      packages=['ris'],
      description='Basic modules used by RIS',
      install_requires=[
            'psycopg2',
            'pyodbc',
            'pandas',
            'requests',
            'xlrd',
            'openpyxl'
      ]
      )

# to package run (setup.py sdist) from cmd
# to install unzip, and run (python setup.py install) from the cmd in the folder