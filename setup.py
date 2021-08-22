from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name="total_connect_client",
    py_modules=["total_connect_client"],
    version="2021.08.2",
    description="Interact with Total Connect 2 alarm systems",
    author="Craig J. Midwinter",
    author_email="craig.j.midwinter@gmail.com",
    url="https://github.com/craigjmidwinter/total-connect-client",
    download_url="https://github.com/craigjmidwinter/total-connect-client",
    keywords=["alarm", "TotalConnect"],
    package_data={"": ["data/*.json"]},
    install_requires=["zeep"],
    packages=["total_connect_client"],
    include_package_data=True,  # use MANIFEST.in during install
    zip_safe=False,
)
