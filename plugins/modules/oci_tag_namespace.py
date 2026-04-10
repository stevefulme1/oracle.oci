#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI tag namespaces."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_tag_namespace
short_description: Manage OCI tag namespaces
description:
    - Create, update, and delete tag namespaces in Oracle Cloud Infrastructure.
    - Tag namespaces act as containers for tag key definitions.
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    compartment_id:
        description:
            - The OCID of the compartment where the tag namespace will be created.
            - Required when creating a new tag namespace.
        type: str
    name:
        description:
            - The name of the tag namespace. Must be unique across all tag
              namespaces in the tenancy.
            - Required when creating a new tag namespace.
        type: str
    description:
        description:
            - The description of the tag namespace.
            - Required when creating a new tag namespace.
        type: str
    is_retired:
        description:
            - Whether the tag namespace is retired.
            - Retired tag namespaces cannot be used to tag resources.
        type: bool
    tag_namespace_id:
        description:
            - The OCID of the tag namespace to update or delete.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the tag namespace.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a tag namespace
  oracle.oci.oci_tag_namespace:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "CostCenter"
    description: "Tag namespace for cost center tracking"
    state: present

- name: Retire a tag namespace
  oracle.oci.oci_tag_namespace:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    is_retired: true
    state: present

- name: Delete a tag namespace
  oracle.oci.oci_tag_namespace:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The tag namespace details.
    returned: on success
    type: dict
    contains:
        id:
            description: The OCID of the tag namespace.
            type: str
        compartment_id:
            description: The OCID of the compartment.
            type: str
        name:
            description: The name of the tag namespace.
            type: str
        description:
            description: The description of the tag namespace.
            type: str
        is_retired:
            description: Whether the tag namespace is retired.
            type: bool
        lifecycle_state:
            description: The current lifecycle state of the tag namespace.
            type: str
        time_created:
            description: The date and time the tag namespace was created.
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
        CreateTagNamespaceDetails,
        UpdateTagNamespaceDetails,
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
        is_retired=dict(type="bool"),
        tag_namespace_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_existing_resource(client, module):
    """Return the existing tag namespace or None."""
    tag_namespace_id = module.params.get("tag_namespace_id")
    if tag_namespace_id:
        try:
            return call_with_retry(client.get_tag_namespace, tag_namespace_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    compartment_id = module.params.get("compartment_id")
    name = module.params.get("name")
    if compartment_id and name:
        namespaces = call_with_retry(
            client.list_tag_namespaces,
            compartment_id,
        ).data
        for ns in namespaces:
            if ns.name == name and ns.lifecycle_state == LIFECYCLE_ACTIVE:
                return call_with_retry(client.get_tag_namespace, ns.id).data

    return None


def create_resource(client, module):
    """Create a new tag namespace."""
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

    details = CreateTagNamespaceDetails(**kwargs)
    resource = call_with_retry(client.create_tag_namespace, details).data
    return resource


def update_resource(client, module, resource):
    """Update an existing tag namespace."""
    kwargs = {}
    for attr in ("description", "is_retired"):
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

    details = UpdateTagNamespaceDetails(**kwargs)
    resource = call_with_retry(client.update_tag_namespace, resource.id, details).data
    return resource


def delete_resource(client, module, resource):
    """Delete a tag namespace."""
    call_with_retry(client.delete_tag_namespace, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_tag_namespace,
            resource.id,
            target_states={LIFECYCLE_DELETED, "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if any attribute needs updating."""
    for attr in ("description", "is_retired"):
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
            ("state", "absent", ["tag_namespace_id"]),
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
