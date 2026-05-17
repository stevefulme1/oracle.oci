# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DNS resolvers."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dns_resolver
short_description: Manage OCI DNS resolvers
description:
    - Update DNS resolvers in Oracle Cloud Infrastructure.
    - Resolvers are automatically created with VCNs and cannot be created or deleted independently.
    - This module uses the OCI Python SDK C(oci.dns.DnsClient).
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment containing the resolver.
        type: str
    resolver_id:
        description:
            - The OCID of the resolver.
            - Required for update operations.
        type: str
        required: true
    display_name:
        description:
            - The display name of the resolver.
        type: str
    attached_vcn_id:
        description:
            - The OCID of the attached VCN (read-only, used for listing).
        type: str
    state:
        description:
            - The desired state of the resolver.
            - Only C(present) is supported as resolvers are managed by VCN lifecycle.
        type: str
        choices:
            - present
        default: present
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Update a DNS resolver display name
  stevefulme1.oci_cloud.oci_dns_resolver:
    resolver_id: "ocid1.dnsresolver.oc1..example"
    display_name: "my-resolver"
    state: present
"""

RETURN = r"""
resolver:
    description: Details of the DNS resolver.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.dnsresolver.oc1..example"
        display_name: "my-resolver"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.dns import DnsClient
    from oci.dns.models import UpdateResolverDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_resource(client, resolver_id):
    """Get a DNS resolver by OCID."""
    try:
        response = call_with_retry(client.get_resolver, resolver_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def needs_update(params, existing):
    """Check if resolver attributes differ from desired state."""
    for attr in ("display_name",):
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        resolver_id=dict(type="str", required=True),
        display_name=dict(type="str"),
        attached_vcn_id=dict(type="str"),
        state=dict(type="str", choices=["present"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DnsClient)
    params = module.params

    existing = get_resource(client, params["resolver_id"])
    if existing is None:
        module.fail_json(msg=f"Resolver {params['resolver_id']} not found.")

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        update_details = UpdateResolverDetails(
            display_name=params.get("display_name"),
            freeform_tags=params.get("freeform_tags"),
            defined_tags=params.get("defined_tags"),
        )
        try:
            response = call_with_retry(
                client.update_resolver, existing.id, update_details,
            )
            resource = response.data
            resource = wait_for_resource(
                module, client.get_resolver, resource.id, target_states=READY_STATES,
            )
            module.exit_json(changed=True, resolver=to_dict(resource))
        except ServiceError as e:
            module.fail_json(msg=f"Failed to update resolver: {e.message}")
        return

    module.exit_json(changed=False, resolver=to_dict(existing))


if __name__ == "__main__":
    main()
