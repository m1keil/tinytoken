from xml.etree import ElementTree

import requests

STS_ENDPOINT = 'https://sts.amazonaws.com/'


def get_credentials(id_token, role_arn):
    payload = {
        "Action": "AssumeRoleWithWebIdentity",
        "DurationSeconds": 900,
        "RoleArn": role_arn,
        "RoleSessionName": 'awscreds',
        "WebIdentityToken": id_token,
        "Version": "2011-06-15"
    }

    resp = requests.get(url=STS_ENDPOINT, params=payload)

    # Process xml
    root_xml_element = ElementTree.fromstring(resp.content)
    credential_children = root_xml_element.find(
        "./sts:AssumeRoleWithWebIdentityResult/sts:Credentials",
        {"sts": "https://sts.amazonaws.com/doc/2011-06-15/"}
    )
    credentials = dict([(x.tag.split('}')[1], x.text) for x in credential_children])

    return credentials
