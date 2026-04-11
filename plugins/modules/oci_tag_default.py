# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI tag defaults."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_tag_default
short_description: Manage OCI tag defaults
description:
  - Create, update, and delete tag defaults in Oracle Cloud Infrastructure.
  - Tag defaults automatically apply a tag to all new resources created in a compartment.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the tag default applies.
      - Required when creating a new tag default.
    type: str
  tag_default_id:
    description:
      - The OCID of the tag default.
      - Required for update and delete operations.
    type: str
  tag_definition_id:
    description:
      - The OCID of the tag definition.
      - Required when creating a new tag default.
    type: str
  tag_namespace_id:
    description:
      - The OCID of the tag namespace.
    type: str
  value:
    description:
      - The default value for the tag.
      - Required when creating a new tag default.
    type: str
  is_required:
    description:
      - Whether the tag must have a value set when resources are created.
    type: bool
    default: false
  state:
    description:
      - The desired state of the tag default.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a tag default
  oracle.oci.oci_tag_default:
    compartment_id: "ocid1.compartment.oc1..example"
    tag_definition_id: "ocid1.tagdefinition.oc1..example"
    value: "production"
    is_required: false
    state: present

- name: Update a tag default value
  oracle.oci.oci_tag_default:
    tag_default_id: "ocid1.tagdefault.oc1..example"
    value: "staging"
    state: present

- name: Delete a tag default
  oracle.oci.oci_tag_default:
    tag_default_id: "ocid1.tagdefault.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The tag default details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the tag default.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    tag_definition_id:
      description: The OCID of the tag definition.
      type: str
    tag_namespace_id:
      description: The OCID of the tag namespace.
      type: str
    value:
      description: The default tag value.
      type: str
    is_required:
      description: Whether the tag is required.
      type: bool
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the tag default was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateTagDefaultDetails,
        UpdateTagDefaultDetails,
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
        result[key] = value
    return result


def get_resource(client, resource_id):
    """Get a tag default by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_tag_default, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, tag_definition_id):
    """Find a tag default by compartment and tag definition."""
    if not compartment_id or not tag_definition_id:
        return None
    resources = call_with_retry(
        client.list_tag_defaults, compartment_id=compartment_id
    ).data
    for r in resources:
        if r.tag_definition_id == tag_definition_id and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new tag default."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        tag_definition_id=module.params["tag_definition_id"],
        value=module.params["value"],
    )
    if module.params.get("is_required") is not None:
        kwargs["is_required"] = module.params["is_required"]

    details = CreateTagDefaultDetails(**kwargs)
    response = call_with_retry(client.create_tag_default, details)
    return response.data


def update_resource(module, client, resource):
    """Update an existing tag default."""
    kwargs = {}
    if module.params.get("value") is not None:
        if module.params["value"] != getattr(resource, "value", None):
            kwargs["value"] = module.params["value"]
    if module.params.get("is_required") is not None:
        if module.params["is_required"] != getattr(resource, "is_required", None):
            kwargs["is_required"] = module.params["is_required"]

    if not kwargs:
        return resource

    details = UpdateTagDefaultDetails(**kwargs)
    response = call_with_retry(client.update_tag_default, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a tag default."""
    call_with_retry(client.delete_tag_default, resource.id)


def needs_update(module, resource):
    """Check if the tag default needs updating."""
    if module.params.get("value") is not None:
        if module.params["value"] != getattr(resource, "value", None):
            return True
    if module.params.get("is_required") is not None:
        if module.params["is_required"] != getattr(resource, "is_required", None):
            return True
    return False


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        tag_default_id=dict(type="str"),
        tag_definition_id=dict(type="str"),
        tag_namespace_id=dict(type="str"),
        value=dict(type="str"),
        is_required=dict(type="bool", default=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["tag_default_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]
    resource_id = module.params.get("tag_default_id")

    resource = None
    if resource_id:
        resource = get_resource(client, resource_id)
    elif module.params.get("compartment_id") and module.params.get("tag_definition_id"):
        resource = find_resource(client, module.params["compartment_id"], module.params["tag_definition_id"])

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
