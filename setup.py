from setuptools import setup

setup(
    name="tinytoken",
    version="0.1.0",
    description="Command line tool to enable accessing AWS using federated GSuite single sign on",
    python_requires=">=3.6",
    packages=['tinytoken'],
    install_requires=['requests~=2.24'],
    extras_require={
        'dev': [
            'mypy',
            'pylint',
            'black',
        ]
    },
    entry_points={"console_scripts": ["tinytoken=tinytoken.cli:entry_point"]},
)
