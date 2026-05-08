# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Blockchain Platforms."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_blockchain_platform
short_description: Manage Blockchain Platforms in OCI
description:
    - Create, update, and delete Blockchain Platforms in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.blockchain.BlockchainPlatformClient).
version_added: "2.1.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the blockchain platform.
            - Required when creating a new platform.
        type: str
    blockchain_platform_id:
        description:
            - The OCID of an existing blockchain platform.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - The display name of the blockchain platform.
        type: str
    description:
        description:
            - A description of the blockchain platform.
        type: str
    platform_role:
        description:
            - The role of the blockchain platform.
        type: str
        choices:
            - FOUNDER
            - PARTICIPANT
    compute_shape:
        description:
            - The compute shape for the blockchain platform.
        type: str
    idcs_access_token:
        description:
            - IDCS access token for the blockchain platform.
        type: str
    state:
        description:
            - The desired state of the blockchain platform.
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
- name: Create a Blockchain Platform
  stevefulme1.oci_cloud.oci_blockchain_platform:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-blockchain"
    platform_role: "FOUNDER"
    compute_shape: "ENTERPRISE_SMALL"
    idcs_access_token: "token..."
    state: present

- name: Delete a Blockchain Platform
  stevefulme1.oci_cloud.oci_blockchain_platform:
    blockchain_platform_id: "ocid1.blockchainplatform.oc1..example"
    state: absent
"""

RETURN = r"""
blockchain_platform:
    description: Details of the Blockchain Platform.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.blockchainplatform.oc1..example"
        display_name: "my-blockchain"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.blockchain import BlockchainPlatformClient
    from oci.blockchain.models import (
        CreateBlockchainPlatformDetails,
        UpdateBlockchainPlatformDetails,
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
        blockchain_platform_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        platform_role=dict(type="str", choices=["FOUNDER", "PARTICIPANT"]),
        compute_shape=dict(type="str"),
        idcs_access_token=dict(type="str", no_log=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_blockchain_platform, resource_id)
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
            client.list_blockchain_platforms, compartment_id=compartment_id,
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
    create_details = CreateBlockchainPlatformDetails(
        compartment_id=params["compartment_id"],
        display_name=params.get("display_name"),
        description=params.get("description"),
        platform_role=params.get("platform_role"),
        compute_shape=params.get("compute_shape"),
        idcs_access_token=params.get("idcs_access_token"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_blockchain_platform, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_blockchain_platform, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateBlockchainPlatformDetails(
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(
        client.update_blockchain_platform, existing.id, update_details,
    )
    resource = response.data
    resource = wait_for_resource(
        module, client.get_blockchain_platform, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_blockchain_platform, existing.id)
    wait_for_resource(
        module, client.get_blockchain_platform, existing.id, target_states=DEAD_STATES,
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
            ("state", "present", ("compartment_id",), True),
            ("state", "absent", ("blockchain_platform_id",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, BlockchainPlatformClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("blockchain_platform_id"):
        existing = get_resource(client, params["blockchain_platform_id"])
    elif params.get("compartment_id"):
        existing = find_resource(
            client, params["compartment_id"], params.get("display_name"),
        )

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
        module.exit_json(changed=True, blockchain_platform=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, blockchain_platform=to_dict(resource))
        return

    module.exit_json(changed=False, blockchain_platform=to_dict(existing))


if __name__ == "__main__":
    main()
