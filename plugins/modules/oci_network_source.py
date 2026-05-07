# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI network source restrictions."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_network_source
short_description: Manage OCI network source restrictions
description:
  - Create, update, and delete network sources in Oracle Cloud Infrastructure.
  - Network sources define a set of IP addresses or VCN resources that can be
    used to restrict access to OCI resources.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the tenancy (root compartment).
      - Required when creating a new network source.
    type: str
  network_source_id:
    description:
      - The OCID of the network source.
      - Required for update and delete operations.
    type: str
  name:
    description:
      - The name of the network source. Must be unique within the tenancy.
      - Required when creating a new network source.
    type: str
  description:
    description:
      - The description of the network source.
      - Required when creating a new network source.
    type: str
  public_source_list:
    description:
      - A list of allowed public IP address ranges in CIDR notation.
    type: list
    elements: str
  virtual_source_list:
    description:
      - A list of allowed VCN OCID and IP range pairs.
      - Each item should be a dict with C(vcn_id) and C(ip_ranges) keys.
    type: list
    elements: dict
  services:
    description:
      - A list of OCI services allowed to use this network source.
    type: list
    elements: str
  state:
    description:
      - The desired state of the network source.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a network source
  stevefulme1.oci_cloud.oci_network_source:
    compartment_id: "ocid1.tenancy.oc1..example"
    name: "corporate-network"
    description: "Corporate office IPs"
    public_source_list:
      - "203.0.113.0/24"
      - "198.51.100.0/24"
    state: present

- name: Update a network source
  stevefulme1.oci_cloud.oci_network_source:
    network_source_id: "ocid1.networksource.oc1..example"
    description: "Updated corporate IPs"
    public_source_list:
      - "203.0.113.0/24"
    state: present

- name: Delete a network source
  stevefulme1.oci_cloud.oci_network_source:
    network_source_id: "ocid1.networksource.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The network source details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the network source.
      type: str
    compartment_id:
      description: The OCID of the tenancy.
      type: str
    name:
      description: The name of the network source.
      type: str
    description:
      description: The description of the network source.
      type: str
    public_source_list:
      description: List of allowed public IP ranges.
      type: list
    virtual_source_list:
      description: List of allowed VCN sources.
      type: list
    services:
      description: List of allowed services.
      type: list
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the network source was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateNetworkSourceDetails,
        UpdateNetworkSourceDetails,
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
    """Get a network source by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_network_source, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, name):
    """Find a network source by compartment and name."""
    if not compartment_id or not name:
        return None
    resources = call_with_retry(client.list_network_sources, compartment_id).data
    for r in resources:
        if r.name == name and r.lifecycle_state == LIFECYCLE_ACTIVE:
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new network source."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        description=module.params["description"],
    )
    if module.params.get("public_source_list"):
        kwargs["public_source_list"] = module.params["public_source_list"]
    if module.params.get("virtual_source_list"):
        kwargs["virtual_source_list"] = module.params["virtual_source_list"]
    if module.params.get("services"):
        kwargs["services"] = module.params["services"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateNetworkSourceDetails(**kwargs)
    response = call_with_retry(client.create_network_source, details)
    return response.data


def update_resource(module, client, resource):
    """Update an existing network source."""
    kwargs = {}
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            kwargs["description"] = module.params["description"]
    if module.params.get("public_source_list") is not None:
        if module.params["public_source_list"] != getattr(resource, "public_source_list", None):
            kwargs["public_source_list"] = module.params["public_source_list"]
    if module.params.get("virtual_source_list") is not None:
        kwargs["virtual_source_list"] = module.params["virtual_source_list"]
    if module.params.get("services") is not None:
        if module.params["services"] != getattr(resource, "services", None):
            kwargs["services"] = module.params["services"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateNetworkSourceDetails(**kwargs)
    response = call_with_retry(client.update_network_source, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a network source."""
    call_with_retry(client.delete_network_source, resource.id)


def needs_update(module, resource):
    """Check if the network source needs updating."""
    if module.params.get("description") is not None:
        if module.params["description"] != getattr(resource, "description", None):
            return True
    if module.params.get("public_source_list") is not None:
        if module.params["public_source_list"] != getattr(resource, "public_source_list", None):
            return True
    if module.params.get("virtual_source_list") is not None:
        return True
    if module.params.get("services") is not None:
        if module.params["services"] != getattr(resource, "services", None):
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
        network_source_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        public_source_list=dict(type="list", elements="str"),
        virtual_source_list=dict(type="list", elements="dict"),
        services=dict(type="list", elements="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["network_source_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]
    resource_id = module.params.get("network_source_id")

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
