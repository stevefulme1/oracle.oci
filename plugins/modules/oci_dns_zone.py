#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DNS Zones."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_dns_zone
short_description: Manage DNS zones in OCI
description:
    - Create, update, and delete DNS zones in Oracle Cloud Infrastructure.
    - Uses the OCI Python SDK DnsClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the DNS zone.
            - Required for creating a DNS zone.
        type: str
    name:
        description:
            - The name of the DNS zone (e.g., example.com).
            - Required for creating a DNS zone.
        type: str
    zone_type:
        description:
            - The type of the DNS zone.
        type: str
        choices: [PRIMARY, SECONDARY]
        default: PRIMARY
    dns_zone_id:
        description:
            - The OCID of the DNS zone.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the DNS zone.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a DNS zone
  oracle.oci.oci_dns_zone:
    compartment_id: "ocid1.compartment.oc1..example"
    name: "example.com"
    zone_type: PRIMARY
    state: present

- name: Delete a DNS zone
  oracle.oci.oci_dns_zone:
    dns_zone_id: "ocid1.dns-zone.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The DNS zone resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.dns-zone.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        name: "example.com"
        zone_type: "PRIMARY"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.dns import DnsClient
    from oci.dns.models import CreateZoneDetails, UpdateZoneDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciDnsZone(OciResourceBase):
    client_class = DnsClient

    def get_resource(self):
        zone_id = self.module.params.get("dns_zone_id")
        if not zone_id:
            return None
        try:
            return self.client.get_zone(zone_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateZoneDetails(
            compartment_id=self.module.params["compartment_id"],
            name=self.module.params["name"],
            zone_type=self.module.params.get("zone_type", "PRIMARY"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        zone = self.client.create_zone(details).data
        return wait_for_resource(
            self.module,
            self.client.get_zone,
            zone.id,
            target_states={LIFECYCLE_ACTIVE},
        )

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateZoneDetails(**kwargs)
        self.client.update_zone(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_zone,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_zone(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_zone,
                resource.id,
                target_states={LIFECYCLE_DELETED, "DELETED"},
            )

    def _updatable_attributes(self):
        return []


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        name=dict(type="str"),
        zone_type=dict(type="str", default="PRIMARY", choices=["PRIMARY", "SECONDARY"]),
        dns_zone_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_zone = OciDnsZone(module)
    oci_zone.run()


if __name__ == "__main__":
    main()
