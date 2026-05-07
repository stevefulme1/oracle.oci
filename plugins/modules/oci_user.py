# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI IAM users."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_user
short_description: Manage OCI IAM users
description:
    - Create, update, and delete users in Oracle Cloud Infrastructure Identity
      and Access Management (IAM).
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    compartment_id:
        description:
            - The OCID of the tenancy (root compartment).
            - Required when creating a new user.
        type: str
    name:
        description:
            - The name of the user. Must be unique across all users in the tenancy.
            - Required when creating a new user.
        type: str
    description:
        description:
            - The description of the user.
            - Required when creating a new user.
        type: str
    email:
        description:
            - The email address of the user.
        type: str
    user_id:
        description:
            - The OCID of the user to update or delete.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the user.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a user
  stevefulme1.oci_cloud.oci_user:
    compartment_id: "ocid1.tenancy.oc1..example"
    name: "jdoe"
    description: "John Doe - developer"
    email: "jdoe@example.com"
    state: present

- name: Update a user description
  stevefulme1.oci_cloud.oci_user:
    user_id: "ocid1.user.oc1..example"
    description: "John Doe - senior developer"
    state: present

- name: Delete a user
  stevefulme1.oci_cloud.oci_user:
    user_id: "ocid1.user.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The user details.
    returned: on success
    type: dict
    contains:
        id:
            description: The OCID of the user.
            type: str
        compartment_id:
            description: The OCID of the tenancy.
            type: str
        name:
            description: The name of the user.
            type: str
        description:
            description: The description of the user.
            type: str
        email:
            description: The email address of the user.
            type: str
        lifecycle_state:
            description: The current lifecycle state of the user.
            type: str
        time_created:
            description: The date and time the user was created.
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
        CreateUserDetails,
        UpdateUserDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        email=dict(type="str"),
        user_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_existing_resource(client, module):
    """Return the existing user or None."""
    user_id = module.params.get("user_id")
    if user_id:
        try:
            return call_with_retry(client.get_user, user_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    compartment_id = module.params.get("compartment_id")
    name = module.params.get("name")
    if compartment_id and name:
        users = call_with_retry(
            client.list_users,
            compartment_id,
        ).data
        for user in users:
            if user.name == name and user.lifecycle_state == LIFECYCLE_ACTIVE:
                return user

    return None


def create_resource(client, module):
    """Create a new user."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        description=module.params["description"],
    )
    if module.params.get("email"):
        kwargs["email"] = module.params["email"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateUserDetails(**kwargs)
    resource = call_with_retry(client.create_user, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_user,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def update_resource(client, module, resource):
    """Update an existing user."""
    kwargs = {}
    for attr in ("description", "email"):
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

    details = UpdateUserDetails(**kwargs)
    resource = call_with_retry(client.update_user, resource.id, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_user,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def delete_resource(client, module, resource):
    """Delete a user."""
    call_with_retry(client.delete_user, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_user,
            resource.id,
            target_states={LIFECYCLE_DELETED, "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if any attribute needs updating."""
    for attr in ("description", "email"):
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
            ("state", "absent", ["user_id"]),
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
