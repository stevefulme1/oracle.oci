# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Identity Domains."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_identity_domain
short_description: Manage OCI Identity Domains
description:
  - Create, update, and delete Identity Domains in Oracle Cloud Infrastructure.
  - Identity Domains provide identity management and authentication services.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the domain resides.
      - Required when creating a new domain.
    type: str
  domain_id:
    description:
      - The OCID of the identity domain.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the domain.
      - Required when creating a new domain.
    type: str
  description:
    description:
      - The description of the domain.
      - Required when creating a new domain.
    type: str
  home_region:
    description:
      - The region where the domain is created.
      - Required when creating a new domain.
    type: str
  license_type:
    description:
      - The license type for the domain.
      - Required when creating a new domain.
    type: str
    choices: [free, oracle-apps-premium, premium, external-user]
  is_hidden_on_login:
    description:
      - Whether the domain is hidden on the login page.
    type: bool
  state:
    description:
      - The desired state of the domain.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create an identity domain
  stevefulme1.oci_cloud.oci_identity_domain:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-domain"
    description: "Development identity domain"
    home_region: "us-ashburn-1"
    license_type: free
    state: present

- name: Update an identity domain
  stevefulme1.oci_cloud.oci_identity_domain:
    domain_id: "ocid1.domain.oc1..example"
    description: "Updated description"
    is_hidden_on_login: true
    state: present

- name: Delete an identity domain
  stevefulme1.oci_cloud.oci_identity_domain:
    domain_id: "ocid1.domain.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The identity domain details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the domain.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the domain.
      type: str
    description:
      description: The description of the domain.
      type: str
    home_region:
      description: The home region of the domain.
      type: str
    license_type:
      description: The license type.
      type: str
    is_hidden_on_login:
      description: Whether the domain is hidden on login.
      type: bool
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the domain was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.identity import IdentityClient
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_resource(client, resource_id):
    """Get a domain by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_domain, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a domain by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    resources = call_with_retry(
        client.list_domains, compartment_id=compartment_id, display_name=display_name
    ).data
    items = resources.items if hasattr(resources, "items") else resources
    for r in items:
        if r.display_name == display_name and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new identity domain."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        description=module.params["description"],
        home_region=module.params["home_region"],
        license_type=module.params["license_type"],
    )
    if module.params.get("is_hidden_on_login") is not None:
        kwargs["is_hidden_on_login"] = module.params["is_hidden_on_login"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = oci.identity.models.CreateDomainDetails(**kwargs)
    response = call_with_retry(client.create_domain, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_domain, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing identity domain."""
    kwargs = {}
    for attr in ("display_name", "description"):
        value = module.params.get(attr)
        if value is not None and value != getattr(resource, attr, None):
            kwargs[attr] = value
    if module.params.get("is_hidden_on_login") is not None:
        if module.params["is_hidden_on_login"] != getattr(resource, "is_hidden_on_login", None):
            kwargs["is_hidden_on_login"] = module.params["is_hidden_on_login"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = oci.identity.models.UpdateDomainDetails(**kwargs)
    response = call_with_retry(client.update_domain, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete an identity domain."""
    call_with_retry(client.delete_domain, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_domain, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the domain needs updating."""
    for attr in ("display_name", "description"):
        desired = module.params.get(attr)
        if desired is not None and desired != getattr(resource, attr, None):
            return True
    if module.params.get("is_hidden_on_login") is not None:
        if module.params["is_hidden_on_login"] != getattr(resource, "is_hidden_on_login", None):
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
        domain_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        home_region=dict(type="str"),
        license_type=dict(type="str", choices=["free", "oracle-apps-premium", "premium", "external-user"]),
        is_hidden_on_login=dict(type="bool"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["domain_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]
    resource_id = module.params.get("domain_id")

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
