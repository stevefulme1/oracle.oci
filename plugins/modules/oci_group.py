# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI IAM groups."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_group
short_description: Manage OCI IAM groups
description:
    - Create, update, and delete groups in Oracle Cloud Infrastructure Identity
      and Access Management (IAM).
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    compartment_id:
        description:
            - The OCID of the tenancy (root compartment).
            - Required when creating a new group.
        type: str
    name:
        description:
            - The name of the group. Must be unique across all groups in the tenancy.
            - Required when creating a new group.
        type: str
    description:
        description:
            - The description of the group.
            - Required when creating a new group.
        type: str
    group_id:
        description:
            - The OCID of the group to update or delete.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the group.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a group
  oracle.oci.oci_group:
    compartment_id: "ocid1.tenancy.oc1..example"
    name: "developers"
    description: "Developer team group"
    state: present

- name: Update a group description
  oracle.oci.oci_group:
    group_id: "ocid1.group.oc1..example"
    description: "Updated developer group description"
    state: present

- name: Delete a group
  oracle.oci.oci_group:
    group_id: "ocid1.group.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The group details.
    returned: on success
    type: dict
    contains:
        id:
            description: The OCID of the group.
            type: str
        compartment_id:
            description: The OCID of the tenancy.
            type: str
        name:
            description: The name of the group.
            type: str
        description:
            description: The description of the group.
            type: str
        lifecycle_state:
            description: The current lifecycle state of the group.
            type: str
        time_created:
            description: The date and time the group was created.
            type: str
        freeform_tags:
            description: Free-form tags for this resource.
            type: dict
        defined_tags:
            description: Defined tags for this resource.
            type: dict
"""

try:
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateGroupDetails,
        UpdateGroupDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        group_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_existing_resource(client, module):
    """Return the existing group or None."""
    group_id = module.params.get("group_id")
    if group_id:
        try:
            return call_with_retry(client.get_group, group_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    compartment_id = module.params.get("compartment_id")
    name = module.params.get("name")
    if compartment_id and name:
        groups = call_with_retry(
            client.list_groups,
            compartment_id,
        ).data
        for group in groups:
            if group.name == name and group.lifecycle_state == LIFECYCLE_ACTIVE:
                return group

    return None


def create_resource(client, module):
    """Create a new group."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        description=module.params["description"],
    )
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateGroupDetails(**kwargs)
    resource = call_with_retry(client.create_group, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_group,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def update_resource(client, module, resource):
    """Update an existing group."""
    kwargs = {}
    if (module.params.get("description") is not None
            and module.params["description"] != getattr(resource, "description", None)):
        kwargs["description"] = module.params["description"]

    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateGroupDetails(**kwargs)
    resource = call_with_retry(client.update_group, resource.id, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_group,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def delete_resource(client, module, resource):
    """Delete a group."""
    call_with_retry(client.delete_group, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_group,
            resource.id,
            target_states={LIFECYCLE_DELETED, "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if any attribute needs updating."""
    desired = module.params.get("description")
    if desired is not None and desired != getattr(resource, "description", None):
        return True
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        return True
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        return True
    return False


def to_dict(resource):
    """Convert an OCI resource to a plain dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        result[key] = value
    return result


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["group_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]

    resource = get_existing_resource(client, module)

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(client, module, resource)
        module.exit_json(changed=True)
        return

    # state == present
    if resource is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(client, module)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(module, resource):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(client, module, resource)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(resource))


if __name__ == "__main__":
    main()
