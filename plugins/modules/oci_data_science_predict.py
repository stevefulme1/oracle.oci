# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for OCI Data Science model deployment predictions."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_data_science_predict
short_description: Call an OCI Data Science model deployment for predictions
description:
    - Send prediction requests to a deployed OCI Data Science model endpoint.
    - This is an B(action) module that calls model inference APIs and returns results.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.data_science.DataScienceClient) to invoke
      the model deployment predict endpoint.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    endpoint_url:
        description:
            - The full URL of the model deployment predict endpoint.
            - Typically in the form C(https://modeldeployment.<region>.oci.customer-oci.com/ocid1.datasciencemodeldeployment.oc1.../predict).
        type: str
        required: true
    data:
        description:
            - The prediction payload to send to the model.
            - Can be a dictionary or a list, depending on what the model expects.
        type: raw
        required: true
    content_type:
        description:
            - The Content-Type header for the prediction request.
        type: str
        default: "application/json"
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Get predictions from a deployed model
  oracle.oci.oci_data_science_predict:
    endpoint_url: "https://modeldeployment.us-ashburn-1.oci.customer-oci.com/ocid1.datasciencemodeldeployment.oc1..example/predict"
    data:
      instances:
        - feature1: 1.5
          feature2: 2.3
          feature3: 0.8
        - feature1: 3.1
          feature2: 1.2
          feature3: 2.5
  register: prediction_result

- name: Send a list payload
  oracle.oci.oci_data_science_predict:
    endpoint_url: "https://modeldeployment.us-ashburn-1.oci.customer-oci.com/ocid1.datasciencemodeldeployment.oc1..example/predict"
    data:
      - [1.5, 2.3, 0.8]
      - [3.1, 1.2, 2.5]
    content_type: "application/json"

- name: Check mode - preview request
  oracle.oci.oci_data_science_predict:
    endpoint_url: "https://modeldeployment.us-ashburn-1.oci.customer-oci.com/ocid1.datasciencemodeldeployment.oc1..example/predict"
    data:
      instances:
        - feature1: 1.0
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured prediction results.
    returned: success
    type: dict
    contains:
        predictions:
            description: The model output (predictions).
            type: raw
        status_code:
            description: HTTP status code from the prediction endpoint.
            type: int
raw_response:
    description: The full response body from the prediction endpoint.
    returned: success
    type: raw
request_payload:
    description: The request payload that was (or would be) sent. Returned in check mode.
    returned: check_mode
    type: dict
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

try:
    import oci
    from oci.signer import Signer
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import get_oci_config


def get_module_args():
    module_args = dict(
        endpoint_url=dict(type="str", required=True),
        data=dict(type="raw", required=True),
        content_type=dict(type="str", default="application/json"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def _create_signer(module):
    """Create an OCI request signer for authenticated HTTP calls."""
    auth_type = module.params.get("auth_type", "api_key")

    if auth_type == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return signer

    if auth_type == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        return signer

    config = get_oci_config(module)
    oci.config.validate_config(config)
    return Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config.get("key_file"),
        pass_phrase=config.get("pass_phrase"),
    )


def _call_predict(module, endpoint_url, data, content_type, max_retries=3):
    """Call the prediction endpoint with OCI signature auth and retry."""
    import time

    signer = _create_signer(module)
    body = json.dumps(data) if not isinstance(data, str) else data

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            # Build signed headers
            import urllib.parse
            parsed = urllib.parse.urlparse(endpoint_url)
            headers = {
                "Content-Type": content_type,
                "host": parsed.netloc,
            }

            # Use the OCI SDK's request signing
            import requests as req_lib
            session = req_lib.Session()
            request = req_lib.Request(
                method="POST",
                url=endpoint_url,
                data=body,
                headers=headers,
            )
            prepared = request.prepare()
            signer(prepared)

            response = session.send(prepared, timeout=120)

            try:
                response_body = response.json()
            except (ValueError, json.JSONDecodeError):
                response_body = response.text

            return response.status_code, response_body

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            raise

    raise last_error


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    endpoint_url = params["endpoint_url"]
    data = params["data"]
    content_type = params["content_type"]

    payload_info = {
        "endpoint_url": endpoint_url,
        "content_type": content_type,
        "data": data,
    }

    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_info,
            result={"predictions": None, "status_code": None},
            raw_response={},
        )

    try:
        status_code, response_body = _call_predict(
            module, endpoint_url, data, content_type,
        )

        # Extract predictions from common response formats
        predictions = response_body
        if isinstance(response_body, dict):
            predictions = response_body.get("predictions", response_body.get("result", response_body))

        result = {
            "predictions": predictions,
            "status_code": status_code,
        }

        if status_code >= 400:
            module.fail_json(
                msg=f"Prediction endpoint returned HTTP {status_code}",
                result=result,
                raw_response=response_body,
                request_payload=payload_info,
            )

        module.exit_json(
            changed=False,
            result=result,
            raw_response=response_body,
        )
    except Exception as e:
        module.fail_json(
            msg=f"OCI Data Science prediction failed: {str(e)}",
            request_payload=payload_info,
        )


if __name__ == "__main__":
    main()
