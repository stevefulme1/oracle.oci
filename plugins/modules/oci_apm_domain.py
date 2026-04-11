# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI APM Domains."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_apm_domain
short_description: Manage OCI APM Domains
description:
  - Create, update, and delete Application Performance Monitoring (APM) domains in OCI.
  - APM domains provide distributed tracing and synthetic monitoring capabilities.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment.
      - Required when creating.
    type: str
  apm_domain_id:
    description:
      - The OCID of the APM domain.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the APM domain.
      - Required when creating.
    type: str
  description:
    description:
      - A description of the APM domain.
    type: str
  is_free_tier:
    description:
      - Whether this is a free-tier APM domain.
    type: bool
    default: false
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
  state:
    description:
      - The desired state of the APM domain.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an APM domain
  oracle.oci.oci_apm_domain:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-apm-domain"
    description: "Production APM domain"
    is_free_tier: false
    state: present

- name: Create a free-tier APM domain
  oracle.oci.oci_apm_domain:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "dev-apm-domain"
    is_free_tier: true
    state: present

- name: Delete an APM domain
  oracle.oci.oci_apm_domain:
    apm_domain_id: "ocid1.apmdomain.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The APM domain details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the APM domain.
      type: str
    display_name:
      description: The display name of the APM domain.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    description:
      description: The description of the APM domain.
      type: str
    is_free_tier:
      description: Whether this is a free-tier domain.
      type: bool
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    data_upload_endpoint:
      description: The endpoint for uploading data.
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
    from oci.apm_control_plane import ApmDomainClient
    from oci.apm_control_plane.models import (
        CreateApmDomainDetails,
        UpdateApmDomainDetails,
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


def get_apm_domain(client, apm_domain_id):
    """Get an APM domain by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_apm_domain, apm_domain_id)
        domain = response.data
        if domain.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return domain
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_apm_domain(client, compartment_id, display_name):
    """Find an APM domain by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    domains = call_with_retry(
        client.list_apm_domains,
        compartment_id,
    ).data
    for d in domains:
        if d.display_name == display_name and d.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_apm_domain(client, d.id)
    return None


def create_apm_domain(module, client):
    """Create a new APM domain."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateApmDomainDetails(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        description=module.params.get("description"),
        is_free_tier=module.params.get("is_free_tier", False),
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_apm_domain, details)
    response.headers.get("opc-work-request-id")

    # Find the created domain by name
    domains = call_with_retry(
        client.list_apm_domains,
        module.params["compartment_id"],
        display_name=module.params["display_name"],
    ).data
    for d in domains:
        if d.display_name == module.params["display_name"]:
            if module.params.get("wait", True):
                return wait_for_resource(
                    module, client.get_apm_domain, d.id, target_states={"ACTIVE"},
                )
            return get_apm_domain(client, d.id)
    return None


def update_apm_domain(module, client, domain):
    """Update an existing APM domain."""
    kwargs = {}
    for attr in ("display_name", "description"):
        value = module.params.get(attr)
        if value is not None:
            kwargs[attr] = value
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return domain

    details = UpdateApmDomainDetails(**kwargs)
    call_with_retry(client.update_apm_domain, domain.id, details)
    return get_apm_domain(client, domain.id)


def delete_apm_domain(module, client, domain):
    """Delete an APM domain."""
    call_with_retry(client.delete_apm_domain, domain.id)


def needs_update(module, domain):
    """Check if the APM domain needs updating."""
    for attr in ("display_name", "description"):
        desired = module.params.get(attr)
        if desired is not None and getattr(domain, attr, None) != desired:
            return True
    if module.params.get("freeform_tags") is not None:
        if getattr(domain, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(domain, "defined_tags", None) != module.params["defined_tags"]:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        apm_domain_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        is_free_tier=dict(type="bool", default=False),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ApmDomainClient)
    state = module.params.get("state", "present")
    apm_domain_id = module.params.get("apm_domain_id")

    # Get existing resource
    domain = None
    if apm_domain_id:
        domain = get_apm_domain(client, apm_domain_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        domain = find_apm_domain(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if domain is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_apm_domain(module, client, domain)
        module.exit_json(changed=True)
        return

    # state == present
    if domain is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id and display_name are required to create an APM domain.")
        if module.check_mode:
            module.exit_json(changed=True)
        domain = create_apm_domain(module, client)
        module.exit_json(changed=True, resource=to_dict(domain))
        return

    if needs_update(module, domain):
        if module.check_mode:
            module.exit_json(changed=True)
        domain = update_apm_domain(module, client, domain)
        module.exit_json(changed=True, resource=to_dict(domain))
        return

    module.exit_json(changed=False, resource=to_dict(domain))


def main():
    run_module()


if __name__ == "__main__":
    main()
