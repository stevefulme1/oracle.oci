# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI AI Vision Document Jobs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_vision_document_job
short_description: Manage AI Vision Document Analysis Jobs in OCI
description:
    - Create AI Vision Document Analysis Jobs in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.ai_vision.AIServiceVisionClient).
    - This is a create-only resource; update and delete are not supported.
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the document job.
            - Required when creating a new job.
        type: str
    document_job_id:
        description:
            - The OCID of an existing document job.
        type: str
    display_name:
        description:
            - The display name of the document job.
        type: str
    input_location:
        description:
            - The input location details for the document job.
        type: dict
    output_location:
        description:
            - The output location details for the document job.
        type: dict
    features:
        description:
            - The list of requested document analysis features.
        type: list
        elements: dict
    language:
        description:
            - The language of the document for analysis.
        type: str
    state:
        description:
            - The desired state of the document job.
        type: str
        choices:
            - present
            - absent
        default: present
    wait:
        description:
            - Whether to wait for the resource to reach the desired state.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time in seconds to wait for the resource to reach the desired state.
        type: int
        default: 1200
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a Vision Document Analysis job
  stevefulme1.oci_cloud.oci_ai_vision_document_job:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-document-job"
    input_location:
      source_type: "OBJECT_LIST_INLINE_INPUT_LOCATION"
      object_locations:
        - namespace_name: "my-namespace"
          bucket_name: "my-bucket"
          object_name: "document.pdf"
    output_location:
      namespace_name: "my-namespace"
      bucket_name: "my-output-bucket"
      prefix: "results"
    features:
      - feature_type: "TEXT_DETECTION"
      - feature_type: "TABLE_DETECTION"
    state: present
"""

RETURN = r"""
document_job:
    description: Details of the document analysis job.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.aivisiondocumentjob.oc1..example"
        display_name: "my-document-job"
        lifecycle_state: "SUCCEEDED"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ai_vision import AIServiceVisionClient
    from oci.ai_vision.models import CreateDocumentJobDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

SUCCEEDED_STATES = frozenset({"SUCCEEDED", "COMPLETED"})


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        document_job_id=dict(type="str"),
        display_name=dict(type="str"),
        input_location=dict(type="dict"),
        output_location=dict(type="dict"),
        features=dict(type="list", elements="dict"),
        language=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_document_job, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def create_resource(module, client):
    params = module.params
    create_details = CreateDocumentJobDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        input_location=params.get("input_location"),
        output_location=params.get("output_location"),
        features=params.get("features"),
        language=params.get("language"),
    )
    response = call_with_retry(client.create_document_job, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_document_job, resource.id, target_states=SUCCEEDED_STATES,
    )
    return resource


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, AIServiceVisionClient)
    params = module.params
    state = params["state"]

    if state == "absent":
        module.exit_json(changed=False, msg="Document jobs cannot be deleted.")
        return

    existing = None
    if params.get("document_job_id"):
        existing = get_resource(client, params["document_job_id"])

    if existing is not None:
        module.exit_json(changed=False, document_job=to_dict(existing))
        return

    if module.check_mode:
        module.exit_json(changed=True)
    resource = create_resource(module, client)
    module.exit_json(changed=True, document_job=to_dict(resource))


if __name__ == "__main__":
    main()
