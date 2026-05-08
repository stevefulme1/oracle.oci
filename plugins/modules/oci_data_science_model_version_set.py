# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Data Science Model Version Sets."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_data_science_model_version_set
short_description: Manage Data Science Model Version Sets in OCI
description:
    - Create, update, and delete Data Science Model Version Sets in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.data_science.DataScienceClient).
version_added: "2.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the model version set.
            - Required when creating a new model version set.
        type: str
    model_version_set_id:
        description:
            - The OCID of an existing model version set.
            - Required for update and delete operations.
        type: str
    project_id:
        description:
            - The OCID of the Data Science project.
            - Required when creating a new model version set.
        type: str
    display_name:
        description:
            - The display name (name) of the model version set.
            - Required when creating a new model version set.
        type: str
    description:
        description:
            - A description of the model version set.
        type: str
    state:
        description:
            - The desired state of the model version set.
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
- name: Create a Model Version Set
  stevefulme1.oci_cloud.oci_data_science_model_version_set:
    compartment_id: "ocid1.compartment.oc1..example"
    project_id: "ocid1.datascienceproject.oc1..example"
    display_name: "my-model-versions"
    description: "Version set for production models"
    state: present

- name: Delete a Model Version Set
  stevefulme1.oci_cloud.oci_data_science_model_version_set:
    model_version_set_id: "ocid1.datasciencemodelversionset.oc1..example"
    state: absent
"""

RETURN = r"""
model_version_set:
    description: Details of the Model Version Set.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.datasciencemodelversionset.oc1..example"
        name: "my-model-versions"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.data_science import DataScienceClient
    from oci.data_science.models import (
        CreateModelVersionSetDetails,
        UpdateModelVersionSetDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        model_version_set_id=dict(type="str"),
        project_id=dict(type="str"),
        display_name=dict(type="str"),
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
        response = call_with_retry(client.get_model_version_set, resource_id)
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
            client.list_model_version_sets, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateModelVersionSetDetails(
        compartment_id=params["compartment_id"],
        project_id=params["project_id"],
        name=params["display_name"],
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_model_version_set, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_model_version_set, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateModelVersionSetDetails(
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_model_version_set, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_model_version_set, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_model_version_set, existing.id)
    wait_for_resource(
        module, client.get_model_version_set, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    if params.get("description") is not None:
        if getattr(existing, "description", None) != params["description"]:
            return True
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "project_id", "display_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DataScienceClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("model_version_set_id"):
        existing = get_resource(client, params["model_version_set_id"])
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
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, model_version_set=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, model_version_set=to_dict(resource))
        return

    module.exit_json(changed=False, model_version_set=to_dict(existing))


if __name__ == "__main__":
    main()
