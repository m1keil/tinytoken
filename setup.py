from setuptools import setup

setup(
    name="tinytoken",
    version="0.1.0",
    description="Command line tool to enable accessing AWS using federated GSuite single sign on",
    packages=['tinytoken'],
    install_requires=['requests'],
    entry_points={"console_scripts": ["tinytoken=tinytoken.cli:main"]},
)
