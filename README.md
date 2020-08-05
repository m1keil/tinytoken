# tinytoken

A command line tool to generate temporary security credentials via OpenID Connect federation with AWS Cognito IDP.

Follows the [OAuth 2.0 Authorization flow for Native apps as described in RFC 8252](https://tools.ietf.org/html/rfc8252).

Dependencies:
* requests: python's stdlib requires external cacerts to be configured/bundled while `requests` already comes with 
  `certifi`. 

## Installation

Installation in virtualenv is recommended:

```
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install git+https://github.com/m1keil/tinytoken
```
