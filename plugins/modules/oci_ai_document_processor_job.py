# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI AI Document Processor Jobs."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_document_processor_job
short_description: Manage AI Document Processor Jobs in OCI
description:
    - Create AI Document Processor Jobs in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.ai_document.AIServiceDocumentClient).
    - This is a create-only resource; update and delete are not supported.
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the processor job.
            - Required when creating a new job.
        type: str
    processor_job_id:
        description:
            - The OCID of an existing processor job.
        type: str
    display_name:
        description:
            - The display name of the processor job.
        type: str
    input_location:
        description:
            - The input location details for the processor job.
        type: dict
    output_location:
        description:
            - The output location details for the processor job.
        type: dict
    processor_config:
        description:
            - The processor configuration including processor type and features.
        type: dict
    state:
        description:
            - The desired state of the processor job.
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
- name: Create a Document Processor job
  stevefulme1.oci_cloud.oci_ai_document_processor_job:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-processor-job"
    input_location:
      source_type: "OBJECT_STORAGE_LOCATIONS"
      object_locations:
        - namespace_name: "my-namespace"
          bucket_name: "my-bucket"
          object_name: "document.pdf"
    output_location:
      namespace_name: "my-namespace"
      bucket_name: "my-output-bucket"
      prefix: "results"
    processor_config:
      processor_type: "GENERAL"
      features:
        - feature_type: "TEXT_EXTRACTION"
    state: present
"""

RETURN = r"""
processor_job:
    description: Details of the processor job.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.aidocumentprocessorjob.oc1..example"
        display_name: "my-processor-job"
        lifecycle_state: "SUCCEEDED"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ai_document import AIServiceDocumentClient
    from oci.ai_document.models import CreateProcessorJobDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
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
        processor_job_id=dict(type="str"),
        display_name=dict(type="str"),
        input_location=dict(type="dict"),
        output_location=dict(type="dict"),
        processor_config=dict(type="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
            elif hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, dict)):
                result[key] = to_dict(value)
            else:
                result[key] = value
        return result
    return resource


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_processor_job, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def create_resource(module, client):
    params = module.params
    create_details = CreateProcessorJobDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        input_location=params.get("input_location"),
        output_location=params.get("output_location"),
        processor_config=params.get("processor_config"),
    )
    response = call_with_retry(client.create_processor_job, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_processor_job, resource.id, target_states=SUCCEEDED_STATES,
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

    client = create_service_client(module, AIServiceDocumentClient)
    params = module.params
    state = params["state"]

    if state == "absent":
        module.exit_json(changed=False, msg="Processor jobs cannot be deleted.")
        return

    existing = None
    if params.get("processor_job_id"):
        existing = get_resource(client, params["processor_job_id"])

    if existing is not None:
        module.exit_json(changed=False, processor_job=to_dict(existing))
        return

    if module.check_mode:
        module.exit_json(changed=True)
    resource = create_resource(module, client)
    module.exit_json(changed=True, processor_job=to_dict(resource))


if __name__ == "__main__":
    main()
