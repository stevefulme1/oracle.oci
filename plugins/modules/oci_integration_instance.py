# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Integration Instances."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_integration_instance
short_description: Manage Integration Instances in OCI
description:
    - Create, update, and delete Integration Instances in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.integration.IntegrationInstanceClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the integration instance.
            - Required when creating a new instance.
        type: str
    integration_instance_id:
        description:
            - The OCID of an existing integration instance.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the integration instance.
            - Required when creating a new instance.
        type: str
    integration_instance_type:
        description:
            - The type of integration instance.
        type: str
        choices:
            - STANDARD
            - ENTERPRISE
        default: STANDARD
    is_byol:
        description:
            - Whether to use Bring Your Own License.
        type: bool
        default: false
    message_packs:
        description:
            - The number of message packs to allocate.
        type: int
        default: 1
    state:
        description:
            - The desired state of the integration instance.
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
- name: Create an integration instance
  stevefulme1.oci_cloud.oci_integration_instance:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-integration"
    integration_instance_type: STANDARD
    is_byol: false
    message_packs: 1
    state: present

- name: Delete an integration instance
  stevefulme1.oci_cloud.oci_integration_instance:
    integration_instance_id: "ocid1.integrationinstance.oc1..example"
    state: absent
"""

RETURN = r"""
integration_instance:
    description: Details of the integration instance.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.integrationinstance.oc1..example"
        display_name: "my-integration"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.integration import IntegrationInstanceClient
    from oci.integration.models import (
        CreateIntegrationInstanceDetails,
        UpdateIntegrationInstanceDetails,
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
        integration_instance_id=dict(type="str"),
        display_name=dict(type="str"),
        integration_instance_type=dict(
            type="str", choices=["STANDARD", "ENTERPRISE"], default="STANDARD",
        ),
        is_byol=dict(type="bool", default=False),
        message_packs=dict(type="int", default=1),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_integration_instance, resource_id)
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
            client.list_integration_instances, compartment_id=compartment_id,
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
    create_details = CreateIntegrationInstanceDetails(
        compartment_id=params["compartment_id"],
        display_name=params["display_name"],
        integration_instance_type=params.get("integration_instance_type"),
        is_byol=params.get("is_byol"),
        message_packs=params.get("message_packs"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_integration_instance, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_integration_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateIntegrationInstanceDetails(
        display_name=params.get("display_name"),
        integration_instance_type=params.get("integration_instance_type"),
        is_byol=params.get("is_byol"),
        message_packs=params.get("message_packs"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(
        client.update_integration_instance, existing.id, update_details,
    )
    resource = response.data
    resource = wait_for_resource(
        module, client.get_integration_instance, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_integration_instance, existing.id)
    wait_for_resource(
        module, client.get_integration_instance, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["display_name", "integration_instance_type", "is_byol", "message_packs"]
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

    client = create_service_client(module, IntegrationInstanceClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("integration_instance_id"):
        existing = get_resource(client, params["integration_instance_id"])
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
                module.fail_json(msg=f"Parameter '{req}' is required to create an integration instance.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, integration_instance=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, integration_instance=to_dict(resource))
        return

    module.exit_json(changed=False, integration_instance=to_dict(existing))


if __name__ == "__main__":
    main()
