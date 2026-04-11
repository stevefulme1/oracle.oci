# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Security Zones."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_security_zone
short_description: Manage OCI Security Zones
description:
  - Create, update, and delete security zones in Oracle Cloud Infrastructure.
  - Security zones enforce security policies on compartments to prevent
    insecure configurations.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the security zone resides.
      - Required when creating a new security zone.
    type: str
  security_zone_id:
    description:
      - The OCID of the security zone.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the security zone.
      - Required when creating a new security zone.
    type: str
  security_zone_recipe_id:
    description:
      - The OCID of the security zone recipe to apply.
      - Required when creating a new security zone.
    type: str
  state:
    description:
      - The desired state of the security zone.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a security zone
  oracle.oci.oci_security_zone:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "prod-security-zone"
    security_zone_recipe_id: "ocid1.securityzonerecipe.oc1..example"
    state: present

- name: Update a security zone
  oracle.oci.oci_security_zone:
    security_zone_id: "ocid1.securityzone.oc1..example"
    display_name: "renamed-zone"
    state: present

- name: Delete a security zone
  oracle.oci.oci_security_zone:
    security_zone_id: "ocid1.securityzone.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The security zone details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the security zone.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the security zone.
      type: str
    security_zone_recipe_id:
      description: The OCID of the security zone recipe.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the security zone was created.
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
    from oci.cloud_guard import CloudGuardClient
    from oci.cloud_guard.models import (
        CreateSecurityZoneDetails,
        UpdateSecurityZoneDetails,
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
    """Get a security zone by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_security_zone, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a security zone by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    resources = call_with_retry(
        client.list_security_zones, compartment_id=compartment_id
    ).data
    items = resources.items if hasattr(resources, "items") else resources
    for r in items:
        if r.display_name == display_name and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new security zone."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        security_zone_recipe_id=module.params["security_zone_recipe_id"],
    )
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateSecurityZoneDetails(**kwargs)
    response = call_with_retry(client.create_security_zone, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_security_zone, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing security zone."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        if module.params["display_name"] != getattr(resource, "display_name", None):
            kwargs["display_name"] = module.params["display_name"]
    if module.params.get("security_zone_recipe_id") is not None:
        if module.params["security_zone_recipe_id"] != getattr(resource, "security_zone_recipe_id", None):
            kwargs["security_zone_recipe_id"] = module.params["security_zone_recipe_id"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateSecurityZoneDetails(**kwargs)
    response = call_with_retry(client.update_security_zone, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a security zone."""
    call_with_retry(client.delete_security_zone, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_security_zone, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the security zone needs updating."""
    if module.params.get("display_name") is not None:
        if module.params["display_name"] != getattr(resource, "display_name", None):
            return True
    if module.params.get("security_zone_recipe_id") is not None:
        if module.params["security_zone_recipe_id"] != getattr(resource, "security_zone_recipe_id", None):
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
        security_zone_id=dict(type="str"),
        display_name=dict(type="str"),
        security_zone_recipe_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["security_zone_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, CloudGuardClient)
    state = module.params["state"]
    resource_id = module.params.get("security_zone_id")

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
