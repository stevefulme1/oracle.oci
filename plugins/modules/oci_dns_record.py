# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DNS records."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_dns_record
short_description: Manage OCI DNS records
description:
    - Create, update, and delete DNS records in a zone.
    - This module uses the OCI Python SDK C(oci.dns.DnsClient).
version_added: "2.2.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment containing the zone.
        type: str
    zone_name_or_id:
        description:
            - The name or OCID of the DNS zone.
            - Required for all operations.
        type: str
        required: true
    domain:
        description:
            - The fully qualified domain name for the record.
            - Required for create and update operations.
        type: str
    rtype:
        description:
            - The record type (A, AAAA, CNAME, MX, TXT, etc.).
            - Required for create and update operations.
        type: str
    rdata:
        description:
            - The record data value.
        type: str
    ttl:
        description:
            - The Time To Live in seconds.
        type: int
    state:
        description:
            - The desired state of the DNS record.
        type: str
        choices:
            - present
            - absent
        default: present
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create an A record
  stevefulme1.oci_cloud.oci_dns_record:
    zone_name_or_id: "example.com"
    domain: "app.example.com"
    rtype: "A"
    rdata: "10.0.0.1"
    ttl: 300
    state: present

- name: Delete a DNS record
  stevefulme1.oci_cloud.oci_dns_record:
    zone_name_or_id: "example.com"
    domain: "app.example.com"
    rtype: "A"
    state: absent
"""

RETURN = r"""
dns_record:
    description: Details of the DNS record.
    returned: On success when state is present.
    type: dict
    sample:
        domain: "app.example.com"
        rtype: "A"
        rdata: "10.0.0.1"
        ttl: 300
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.dns import DnsClient
    from oci.dns.models import (
        RecordDetails,
        UpdateDomainRecordsDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry


def get_domain_records(client, zone_name_or_id, domain, rtype, compartment_id=None):
    """Get existing DNS records for a domain and rtype."""
    try:
        kwargs = dict(zone_name_or_id=zone_name_or_id, domain=domain, rtype=rtype)
        if compartment_id:
            kwargs["compartment_id"] = compartment_id
        response = call_with_retry(client.get_domain_records, **kwargs)
        return response.data.items
    except ServiceError as e:
        if e.status == 404:
            return []
        raise


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        zone_name_or_id=dict(type="str", required=True),
        domain=dict(type="str"),
        rtype=dict(type="str"),
        rdata=dict(type="str"),
        ttl=dict(type="int"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("domain", "rtype", "rdata")),
            ("state", "absent", ("domain", "rtype")),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DnsClient)
    params = module.params
    state = params["state"]

    zone = params["zone_name_or_id"]
    domain = params["domain"]
    rtype = params["rtype"]
    compartment_id = params.get("compartment_id")

    existing = get_domain_records(client, zone, domain, rtype, compartment_id)

    if state == "absent":
        if not existing:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        try:
            call_with_retry(
                client.delete_domain_records,
                zone_name_or_id=zone,
                domain=domain,
            )
            module.exit_json(changed=True)
        except ServiceError as e:
            module.fail_json(msg=f"Failed to delete DNS records: {e.message}")
        return

    # state == present
    record = RecordDetails(
        domain=domain,
        rtype=rtype,
        rdata=params["rdata"],
        ttl=params.get("ttl", 300),
    )

    # Check if record already exists with same data
    for rec in existing:
        if rec.rdata == params["rdata"] and rec.ttl == params.get("ttl", rec.ttl):
            module.exit_json(changed=False, dns_record=to_dict(rec))
            return

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        update_details = UpdateDomainRecordsDetails(items=[record])
        kwargs = dict(
            zone_name_or_id=zone,
            domain=domain,
            update_domain_records_details=update_details,
        )
        if compartment_id:
            kwargs["compartment_id"] = compartment_id
        response = call_with_retry(client.update_domain_records, **kwargs)
        results = response.data.items
        module.exit_json(changed=True, dns_record=to_dict(results[0]) if results else {})
    except ServiceError as e:
        module.fail_json(msg=f"Failed to update DNS record: {e.message}")


if __name__ == "__main__":
    main()
