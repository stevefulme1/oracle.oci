# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Web Application Firewalls."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_waf
short_description: Manage OCI Web Application Firewalls
description:
  - Create, update, and delete Web Application Firewalls in Oracle Cloud Infrastructure.
  - A WAF protects web applications by filtering and monitoring HTTP traffic.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the WAF resides.
      - Required when creating a new WAF.
    type: str
  web_app_firewall_id:
    description:
      - The OCID of the Web Application Firewall.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the WAF.
      - Required when creating a new WAF.
    type: str
  backend_type:
    description:
      - The backend type of the WAF.
    type: str
    choices: [LOAD_BALANCER]
    default: LOAD_BALANCER
  web_app_firewall_policy_id:
    description:
      - The OCID of the WAF policy to associate.
      - Required when creating a new WAF.
    type: str
  load_balancer_id:
    description:
      - The OCID of the load balancer to protect.
      - Required when creating a new WAF with LOAD_BALANCER backend type.
    type: str
  state:
    description:
      - The desired state of the WAF.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a Web Application Firewall
  oracle.oci.oci_waf:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-waf"
    web_app_firewall_policy_id: "ocid1.webappfirewallpolicy.oc1..example"
    load_balancer_id: "ocid1.loadbalancer.oc1..example"
    backend_type: LOAD_BALANCER
    state: present

- name: Update a WAF display name
  oracle.oci.oci_waf:
    web_app_firewall_id: "ocid1.webappfirewall.oc1..example"
    display_name: "renamed-waf"
    state: present

- name: Delete a WAF
  oracle.oci.oci_waf:
    web_app_firewall_id: "ocid1.webappfirewall.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The Web Application Firewall details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the WAF.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the WAF.
      type: str
    backend_type:
      description: The backend type.
      type: str
    web_app_firewall_policy_id:
      description: The OCID of the WAF policy.
      type: str
    load_balancer_id:
      description: The OCID of the load balancer.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the WAF was created.
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
    from oci.waf import WafClient
    from oci.waf.models import (
        CreateWebAppFirewallDetails,
        UpdateWebAppFirewallDetails,
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
    """Get a WAF by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_web_app_firewall, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a WAF by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    resources = call_with_retry(
        client.list_web_app_firewalls, compartment_id=compartment_id
    ).data
    items = resources.items if hasattr(resources, "items") else resources
    for r in items:
        if r.display_name == display_name and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new WAF."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        backend_type=module.params.get("backend_type", "LOAD_BALANCER"),
        web_app_firewall_policy_id=module.params["web_app_firewall_policy_id"],
        load_balancer_id=module.params["load_balancer_id"],
    )
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateWebAppFirewallDetails(**kwargs)
    response = call_with_retry(client.create_web_app_firewall, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_web_app_firewall, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing WAF."""
    kwargs = {}
    for attr in ("display_name", "web_app_firewall_policy_id"):
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

    details = UpdateWebAppFirewallDetails(**kwargs)
    response = call_with_retry(client.update_web_app_firewall, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a WAF."""
    call_with_retry(client.delete_web_app_firewall, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_web_app_firewall, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the WAF needs updating."""
    for attr in ("display_name", "web_app_firewall_policy_id"):
        desired = module.params.get(attr)
        if desired is not None and desired != getattr(resource, attr, None):
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
        web_app_firewall_id=dict(type="str"),
        display_name=dict(type="str"),
        backend_type=dict(type="str", choices=["LOAD_BALANCER"], default="LOAD_BALANCER"),
        web_app_firewall_policy_id=dict(type="str"),
        load_balancer_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["web_app_firewall_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, WafClient)
    state = module.params["state"]
    resource_id = module.params.get("web_app_firewall_id")

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
