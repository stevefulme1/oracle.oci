# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Process Automation Instances."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_opa_instance
short_description: Manage OCI Process Automation Instances
description:
    - Create, update, and delete OCI Process Automation Instances in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.opa.OpaInstanceClient).
version_added: "2.1.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the OPA instance.
            - Required when creating a new instance.
        type: str
    opa_instance_id:
        description:
            - The OCID of an existing OPA instance.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the OPA instance.
            - Required when creating a new instance.
        type: str
    description:
        description:
            - A description of the OPA instance.
        type: str
    shape_name:
        description:
            - The shape of the OPA instance.
        type: str
        choices:
            - DEVELOPMENT
            - PRODUCTION
    state:
        description:
            - The desired state of the OPA instance.
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
- name: Create an OPA instance
  stevefulme1.oci_cloud.oci_opa_instance:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-opa-instance"
    shape_name: "DEVELOPMENT"
    state: present

- name: Update an OPA instance
  stevefulme1.oci_cloud.oci_opa_instance:
    opa_instance_id: "ocid1.opainstance.oc1..example"
    display_name: "updated-opa-instance"
    description: "Updated description"
    state: present

- name: Delete an OPA instance
  stevefulme1.oci_cloud.oci_opa_instance:
    opa_instance_id: "ocid1.opainstance.oc1..example"
    state: absent
"""

RETURN = r"""
opa_instance:
    description: Details of the OPA instance.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.opainstance.oc1..example"
        display_name: "my-opa-instance"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.opa import OpaInstanceClient
    from oci.opa.models import (
        CreateOpaInstanceDetails,
        UpdateOpaInstanceDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        opa_instance_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        shape_name=dict(type="str", choices=["DEVELOPMENT", "PRODUCTION"]),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_opa_instance, resource_id)
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
            client.list_opa_instances, compartment_id=compartment_id,
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
    create_details = CreateOpaInstanceDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        description=params.get("description"),
        shape_name=params.get("shape_name"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_opa_instance, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_opa_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateOpaInstanceDetails(
        display_name=params.get("display_name"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_opa_instance, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_opa_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_opa_instance, existing.id)
    wait_for_resource(
        module, client.get_opa_instance, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "description"]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
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
            ("state", "present", ("compartment_id", "display_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, OpaInstanceClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("opa_instance_id"):
        existing = get_resource(client, params["opa_instance_id"])
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
        for req in ("compartment_id", "display_name"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create an OPA instance.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, opa_instance=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, opa_instance=to_dict(resource))
        return

    module.exit_json(changed=False, opa_instance=to_dict(existing))


if __name__ == "__main__":
    main()
