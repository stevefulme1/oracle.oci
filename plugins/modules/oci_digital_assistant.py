# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Digital Assistant Instances."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_digital_assistant
short_description: Manage Digital Assistant Instances in OCI
description:
    - Create, update, and delete Digital Assistant (ODA) Instances in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.oda.OdaClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the ODA instance.
            - Required when creating a new instance.
        type: str
    oda_instance_id:
        description:
            - The OCID of an existing ODA instance.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the ODA instance.
            - Required when creating a new instance.
        type: str
    shape_name:
        description:
            - The shape of the ODA instance.
        type: str
        choices:
            - DEVELOPMENT
            - PRODUCTION
        default: DEVELOPMENT
    description:
        description:
            - A description of the ODA instance.
        type: str
    state:
        description:
            - The desired state of the ODA instance.
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
- name: Create a Digital Assistant instance
  stevefulme1.oci_cloud.oci_digital_assistant:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-oda-instance"
    shape_name: DEVELOPMENT
    state: present

- name: Delete a Digital Assistant instance
  stevefulme1.oci_cloud.oci_digital_assistant:
    oda_instance_id: "ocid1.odainstance.oc1..example"
    state: absent
"""

RETURN = r"""
oda_instance:
    description: Details of the ODA instance.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.odainstance.oc1..example"
        display_name: "my-oda-instance"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.oda import OdaClient
    from oci.oda.models import (
        CreateOdaInstanceDetails,
        UpdateOdaInstanceDetails,
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
        oda_instance_id=dict(type="str"),
        display_name=dict(type="str"),
        shape_name=dict(type="str", choices=["DEVELOPMENT", "PRODUCTION"], default="DEVELOPMENT"),
        description=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_oda_instance, resource_id)
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
            client.list_oda_instances, compartment_id=compartment_id,
        )
        for item in response.data:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if display_name and item.display_name == display_name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateOdaInstanceDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        shape_name=params.get("shape_name"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_oda_instance, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_oda_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateOdaInstanceDetails(
        display_name=params.get("display_name"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_oda_instance, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_oda_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_oda_instance, existing.id)
    wait_for_resource(
        module, client.get_oda_instance, existing.id, target_states=DEAD_STATES,
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

    client = create_service_client(module, OdaClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("oda_instance_id"):
        existing = get_resource(client, params["oda_instance_id"])
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
                module.fail_json(msg=f"Parameter '{req}' is required to create an ODA instance.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, oda_instance=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, oda_instance=to_dict(resource))
        return

    module.exit_json(changed=False, oda_instance=to_dict(existing))


if __name__ == "__main__":
    main()
