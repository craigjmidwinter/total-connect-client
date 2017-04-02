#from distutils.core import setup
from setuptools import setup, find_packages
setup(
  name = 'total-connect-client',
  py_modules = ['total-connect-client'],
  version = '0.02',
  description = 'Interact with Total Connect 2 alarm systems',
  author = 'Craig J. Ward',
  author_email = 'ward.craig.j@gmail.com',
  url = 'https://github.com/wardcraigj/total-connect-client',
  download_url = 'https://github.com/wardcraigj/total-connect-client',
  keywords = ['alarm','TotalConnect'],
  package_data = {'': ['data/*.json']},
  requires = ['requests', 'zeep', 'pprint', 'logging', 'logging.handlers', 'sys'],
  install_requires = [],
#  packages=find_packages(exclude=['tests', 'tests.*']),
  packages=['total-connect-client'],
  include_package_data=True, # use MANIFEST.in during install
  zip_safe=False
)
