from distutils.core import setup
from setuptools import setup

setup(
    name="total_connect_client",
    version="2022.10",
    description="Interact with Total Connect 2 alarm systems",
    author="Craig J. Midwinter",
    author_email="craig.j.midwinter@gmail.com",
    url="https://github.com/craigjmidwinter/total-connect-client",
    download_url="https://github.com/craigjmidwinter/total-connect-client",
    keywords=["alarm", "TotalConnect"],
    package_data={"": ["data/*.json"]},
    install_requires=["zeep>=4.1.0"],
    python_requires=">=3.7",
    packages=["total_connect_client"],
    include_package_data=True,  # use MANIFEST.in during install
    zip_safe=False,
)
