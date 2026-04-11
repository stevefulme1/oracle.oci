# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Generative AI Models."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_generative_ai_model
short_description: Manage Generative AI Models in OCI
description:
    - Create and delete Generative AI Models in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.generative_ai.GenerativeAiClient).
    - This is a create/delete only resource; update is not supported.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the model.
            - Required when creating a new model.
        type: str
    model_id:
        description:
            - The OCID of an existing Generative AI model.
            - Required for delete operations.
        type: str
    display_name:
        description:
            - The display name of the model.
        type: str
    base_model_id:
        description:
            - The OCID of the base model for fine-tuning.
            - Required when creating a new model.
        type: str
    fine_tune_details:
        description:
            - Fine-tuning details for the model.
        type: dict
    description:
        description:
            - A description of the model.
        type: str
    state:
        description:
            - The desired state of the model.
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
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a Generative AI model (fine-tuned)
  oracle.oci.oci_generative_ai_model:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-fine-tuned-model"
    base_model_id: "ocid1.generativeaimodel.oc1..example"
    fine_tune_details:
      training_dataset:
        dataset_type: "OBJECT_STORAGE"
        namespace_name: "my-namespace"
        bucket_name: "my-bucket"
        object_name: "training-data.jsonl"
    state: present

- name: Delete a Generative AI model
  oracle.oci.oci_generative_ai_model:
    model_id: "ocid1.generativeaimodel.oc1..example"
    state: absent
"""

RETURN = r"""
generative_ai_model:
    description: Details of the Generative AI model.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.generativeaimodel.oc1..example"
        display_name: "my-fine-tuned-model"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.generative_ai import GenerativeAiClient
    from oci.generative_ai.models import CreateModelDetails
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        model_id=dict(type="str"),
        display_name=dict(type="str"),
        base_model_id=dict(type="str"),
        fine_tune_details=dict(type="dict"),
        description=dict(type="str"),
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
        response = call_with_retry(client.get_model, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    if not compartment_id:
        return None
    try:
        response = call_with_retry(
            client.list_models, compartment_id=compartment_id,
        )
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateModelDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        base_model_id=params.get("base_model_id"),
        fine_tune_details=params.get("fine_tune_details"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_model, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_model, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_model, existing.id)
    wait_for_resource(
        module, client.get_model, existing.id, target_states=DEAD_STATES,
    )


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "base_model_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, GenerativeAiClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("model_id"):
        existing = get_resource(client, params["model_id"])
    elif params.get("compartment_id"):
        existing = find_resource(client, params["compartment_id"], params.get("display_name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        for req in ("compartment_id", "base_model_id"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a Generative AI model.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, generative_ai_model=to_dict(resource))
        return

    # No update supported for generative AI models
    module.exit_json(changed=False, generative_ai_model=to_dict(existing))


if __name__ == "__main__":
    main()
