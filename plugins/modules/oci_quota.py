# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI compartment quota policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_quota
short_description: Manage OCI compartment quota policies
description:
  - Create, update, and delete quota policies in Oracle Cloud Infrastructure.
  - Quotas control resource consumption within compartments.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment (typically the tenancy root).
      - Required when creating a new quota.
    type: str
  quota_id:
    description:
      - The OCID of the quota.
      - Required for update and delete operations.
    type: str
  name:
    description:
      - The name of the quota. Must be unique within the tenancy.
      - Required when creating a new quota.
    type: str
  description:
    description:
      - The description of the quota.
      - Required when creating a new quota.
    type: str
  statements:
    description:
      - A list of quota policy statements.
      - Required when creating a new quota.
    type: list
    elements: str
  state:
    description:
      - The desired state of the quota.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a quota
  oracle.oci.oci_quota:
    compartment_id: "ocid1.tenancy.oc1..example"
    name: "dev-quota"
    description: "Quota for dev compartment"
    statements:
      - "set compute quota vm-standard-count to 10 in compartment dev"
      - "set compute quota core-count to 40 in compartment dev"
    state: present

- name: Update a quota
  oracle.oci.oci_quota:
    quota_id: "ocid1.quota.oc1..example"
    description: "Updated quota description"
    statements:
      - "set compute quota vm-standard-count to 20 in compartment dev"
    state: present

- name: Delete a quota
  oracle.oci.oci_quota:
    quota_id: "ocid1.quota.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The quota details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the quota.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    name:
      description: The name of the quota.
      type: str
    description:
      description: The description of the quota.
      type: str
    statements:
      description: The list of quota statements.
      type: list
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the quota was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.limits import QuotasClient
    from oci.limits.models import (
        CreateQuotaDetails,
        UpdateQuotaDetails,
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
    """Get a quota by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_quota, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, name):
    """Find a quota by compartment and name."""
    if not compartment_id or not name:
        return None
    resources = call_with_retry(
        client.list_quotas, compartment_id=compartment_id, name=name
    ).data
    items = resources.items if hasattr(resources, "items") else resources
    for r in items:
        if r.name == name and r.lifecycle_state == LIFECYCLE_ACTIVE:
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new quota."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        description=module.params["description"],
        statements=module.params["statements"],
    )
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateQuotaDetails(**kwargs)
    response = call_with_retry(client.create_quota, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_quota, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing quota."""
    kwargs = {}
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            kwargs["description"] = module.params["description"]
    if module.params.get("statements") is not None:
        if module.params["statements"] != getattr(resource, "statements", None):
            kwargs["statements"] = module.params["statements"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateQuotaDetails(**kwargs)
    response = call_with_retry(client.update_quota, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a quota."""
    call_with_retry(client.delete_quota, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_quota, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the quota needs updating."""
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            return True
    if module.params.get("statements") is not None:
        if module.params["statements"] != getattr(resource, "statements", None):
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
        quota_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        statements=dict(type="list", elements="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["quota_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, QuotasClient)
    state = module.params["state"]
    resource_id = module.params.get("quota_id")

    resource = None
    if resource_id:
        resource = get_resource(client, resource_id)
    elif module.params.get("compartment_id") and module.params.get("name"):
        resource = find_resource(client, module.params["compartment_id"], module.params["name"])

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
