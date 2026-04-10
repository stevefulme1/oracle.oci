# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI dynamic groups."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dynamic_group
short_description: Manage OCI dynamic groups
description:
    - Create, update, and delete dynamic groups in Oracle Cloud Infrastructure
      Identity and Access Management (IAM).
    - Dynamic groups allow you to group OCI compute instances and other resources
      as principal actors, similar to user groups.
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    compartment_id:
        description:
            - The OCID of the tenancy (root compartment).
            - Required when creating a new dynamic group.
        type: str
    name:
        description:
            - The name of the dynamic group. Must be unique across all dynamic
              groups in the tenancy.
            - Required when creating a new dynamic group.
        type: str
    description:
        description:
            - The description of the dynamic group.
            - Required when creating a new dynamic group.
        type: str
    matching_rule:
        description:
            - The matching rule that defines which resources belong to the
              dynamic group.
            - "Example: C(Any {instance.compartment.id = 'ocid1.compartment.oc1..example'})"
            - Required when creating a new dynamic group.
        type: str
    dynamic_group_id:
        description:
            - The OCID of the dynamic group to update or delete.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the dynamic group.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a dynamic group for compute instances
  oracle.oci.oci_dynamic_group:
    compartment_id: "ocid1.tenancy.oc1..example"
    name: "web-instances"
    description: "Dynamic group for web server instances"
    matching_rule: "Any {instance.compartment.id = 'ocid1.compartment.oc1..example'}"
    state: present

- name: Update matching rule
  oracle.oci.oci_dynamic_group:
    dynamic_group_id: "ocid1.dynamicgroup.oc1..example"
    matching_rule: "All {instance.compartment.id = 'ocid1.compartment.oc1..new'}"
    state: present

- name: Delete a dynamic group
  oracle.oci.oci_dynamic_group:
    dynamic_group_id: "ocid1.dynamicgroup.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The dynamic group details.
    returned: on success
    type: dict
    contains:
        id:
            description: The OCID of the dynamic group.
            type: str
        compartment_id:
            description: The OCID of the tenancy.
            type: str
        name:
            description: The name of the dynamic group.
            type: str
        description:
            description: The description of the dynamic group.
            type: str
        matching_rule:
            description: The matching rule for the dynamic group.
            type: str
        lifecycle_state:
            description: The current lifecycle state of the dynamic group.
            type: str
        time_created:
            description: The date and time the dynamic group was created.
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
        CreateDynamicGroupDetails,
        UpdateDynamicGroupDetails,
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
        matching_rule=dict(type="str"),
        dynamic_group_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_existing_resource(client, module):
    """Return the existing dynamic group or None."""
    dynamic_group_id = module.params.get("dynamic_group_id")
    if dynamic_group_id:
        try:
            return call_with_retry(client.get_dynamic_group, dynamic_group_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    compartment_id = module.params.get("compartment_id")
    name = module.params.get("name")
    if compartment_id and name:
        groups = call_with_retry(
            client.list_dynamic_groups,
            compartment_id,
        ).data
        for group in groups:
            if group.name == name and group.lifecycle_state == LIFECYCLE_ACTIVE:
                return group

    return None


def create_resource(client, module):
    """Create a new dynamic group."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        description=module.params["description"],
        matching_rule=module.params["matching_rule"],
    )
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateDynamicGroupDetails(**kwargs)
    resource = call_with_retry(client.create_dynamic_group, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_dynamic_group,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def update_resource(client, module, resource):
    """Update an existing dynamic group."""
    kwargs = {}
    for attr in ("description", "matching_rule"):
        value = module.params.get(attr)
        if value is not None and value != getattr(resource, attr, None):
            kwargs[attr] = value

    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateDynamicGroupDetails(**kwargs)
    resource = call_with_retry(client.update_dynamic_group, resource.id, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_dynamic_group,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def delete_resource(client, module, resource):
    """Delete a dynamic group."""
    call_with_retry(client.delete_dynamic_group, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_dynamic_group,
            resource.id,
            target_states={LIFECYCLE_DELETED, "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if any attribute needs updating."""
    for attr in ("description", "matching_rule"):
        desired = module.params.get(attr)
        if desired is not None and desired != getattr(resource, attr, None):
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
            ("state", "absent", ["dynamic_group_id"]),
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
