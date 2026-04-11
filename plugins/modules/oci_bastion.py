# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Bastion Service."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_bastion
short_description: Manage OCI Bastion Service
description:
  - Create, update, and delete bastions in Oracle Cloud Infrastructure.
  - Bastions provide restricted and time-limited access to target resources.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the bastion resides.
      - Required when creating a new bastion.
    type: str
  bastion_id:
    description:
      - The OCID of the bastion.
      - Required for update and delete operations.
    type: str
  bastion_type:
    description:
      - The type of bastion.
      - Required when creating a new bastion.
    type: str
    choices: [STANDARD]
    default: STANDARD
  target_subnet_id:
    description:
      - The OCID of the subnet the bastion connects to.
      - Required when creating a new bastion.
    type: str
  display_name:
    description:
      - A user-friendly name for the bastion.
    type: str
  client_cidr_block_allow_list:
    description:
      - List of CIDR blocks allowed to connect to the bastion.
    type: list
    elements: str
  max_session_ttl_in_seconds:
    description:
      - Maximum time-to-live for bastion sessions in seconds.
    type: int
  state:
    description:
      - The desired state of the bastion.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a bastion
  oracle.oci.oci_bastion:
    compartment_id: "ocid1.compartment.oc1..example"
    bastion_type: STANDARD
    target_subnet_id: "ocid1.subnet.oc1..example"
    display_name: "my-bastion"
    client_cidr_block_allow_list:
      - "10.0.0.0/24"
    max_session_ttl_in_seconds: 10800
    state: present

- name: Update a bastion
  oracle.oci.oci_bastion:
    bastion_id: "ocid1.bastion.oc1..example"
    max_session_ttl_in_seconds: 7200
    state: present

- name: Delete a bastion
  oracle.oci.oci_bastion:
    bastion_id: "ocid1.bastion.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The bastion details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the bastion.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the bastion.
      type: str
    bastion_type:
      description: The type of bastion.
      type: str
    target_subnet_id:
      description: The OCID of the target subnet.
      type: str
    client_cidr_block_allow_list:
      description: Allowed CIDR blocks.
      type: list
    max_session_ttl_in_seconds:
      description: Maximum session TTL.
      type: int
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the bastion was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.bastion import BastionClient
    from oci.bastion.models import (
        CreateBastionDetails,
        UpdateBastionDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def to_dict(resource):
    """Convert an OCI SDK resource to a serializable dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            result[key] = to_dict(value)
        elif isinstance(value, list):
            result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
        else:
            result[key] = value
    return result


def get_resource(client, resource_id):
    """Get a bastion by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_bastion, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a bastion by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    resources = call_with_retry(
        client.list_bastions, compartment_id=compartment_id
    ).data
    items = resources if isinstance(resources, list) else resources.items
    for r in items:
        if r.name == display_name and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new bastion."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        bastion_type=module.params.get("bastion_type", "STANDARD"),
        target_subnet_id=module.params["target_subnet_id"],
    )
    if module.params.get("display_name"):
        kwargs["name"] = module.params["display_name"]
    if module.params.get("client_cidr_block_allow_list"):
        kwargs["client_cidr_block_allow_list"] = module.params["client_cidr_block_allow_list"]
    if module.params.get("max_session_ttl_in_seconds"):
        kwargs["max_session_ttl_in_seconds"] = module.params["max_session_ttl_in_seconds"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateBastionDetails(**kwargs)
    response = call_with_retry(client.create_bastion, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_bastion, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing bastion."""
    kwargs = {}
    if module.params.get("max_session_ttl_in_seconds") is not None:
        if module.params["max_session_ttl_in_seconds"] != getattr(resource, "max_session_ttl_in_seconds", None):
            kwargs["max_session_ttl_in_seconds"] = module.params["max_session_ttl_in_seconds"]
    if module.params.get("client_cidr_block_allow_list") is not None:
        if module.params["client_cidr_block_allow_list"] != getattr(resource, "client_cidr_block_allow_list", None):
            kwargs["client_cidr_block_allow_list"] = module.params["client_cidr_block_allow_list"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateBastionDetails(**kwargs)
    response = call_with_retry(client.update_bastion, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a bastion."""
    call_with_retry(client.delete_bastion, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_bastion, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the bastion needs updating."""
    if module.params.get("max_session_ttl_in_seconds") is not None:
        if module.params["max_session_ttl_in_seconds"] != getattr(resource, "max_session_ttl_in_seconds", None):
            return True
    if module.params.get("client_cidr_block_allow_list") is not None:
        if module.params["client_cidr_block_allow_list"] != getattr(resource, "client_cidr_block_allow_list", None):
            return True
    freeform_tags = module.params.get("freeform_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        return True
    defined_tags = module.params.get("defined_tags")
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        return True
    return False


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        bastion_id=dict(type="str"),
        bastion_type=dict(type="str", choices=["STANDARD"], default="STANDARD"),
        target_subnet_id=dict(type="str"),
        display_name=dict(type="str"),
        client_cidr_block_allow_list=dict(type="list", elements="str"),
        max_session_ttl_in_seconds=dict(type="int"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["bastion_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, BastionClient)
    state = module.params["state"]
    resource_id = module.params.get("bastion_id")

    resource = None
    if resource_id:
        resource = get_resource(client, resource_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        resource = find_resource(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, resource)
        module.exit_json(changed=True)
        return

    if resource is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(module, resource):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, resource)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(resource))


if __name__ == "__main__":
    main()
