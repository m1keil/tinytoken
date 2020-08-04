from setuptools import setup, find_packages

setup(
    name="tinytoken",
    description="Command line tool to enable accessing AWS using federated GSuite single sign on",
    entry_points={"console_scripts": ["tinytoken=tinytoken.cli:main"]},
    install_requires=['requests'],
    packages=find_packages(where='tinytoken')
)
