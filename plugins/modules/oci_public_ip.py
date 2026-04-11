# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Public IPs."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_public_ip
short_description: Manage public IPs in OCI
description:
    - Create, update, and delete public IP addresses in Oracle Cloud Infrastructure.
    - Supports both reserved (static) and ephemeral public IPs.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the public IP.
            - Required for creating a public IP.
        type: str
    public_ip_id:
        description:
            - The OCID of the public IP.
            - Required for update and delete operations.
        type: str
    lifetime:
        description:
            - Whether the public IP is reserved or ephemeral.
            - Required for creating a public IP.
        type: str
        choices: [RESERVED, EPHEMERAL]
    display_name:
        description:
            - A user-friendly name for the public IP.
        type: str
    private_ip_id:
        description:
            - The OCID of the private IP to assign the public IP to.
            - Required for ephemeral public IPs.
        type: str
    state:
        description:
            - The desired state of the public IP.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a reserved public IP
  oracle.oci.oci_public_ip:
    compartment_id: "ocid1.compartment.oc1..example"
    lifetime: "RESERVED"
    display_name: "my-reserved-ip"
    state: present

- name: Create an ephemeral public IP assigned to a private IP
  oracle.oci.oci_public_ip:
    compartment_id: "ocid1.compartment.oc1..example"
    lifetime: "EPHEMERAL"
    private_ip_id: "ocid1.privateip.oc1..example"
    display_name: "my-ephemeral-ip"
    state: present

- name: Assign a reserved public IP to a private IP
  oracle.oci.oci_public_ip:
    public_ip_id: "ocid1.publicip.oc1..example"
    private_ip_id: "ocid1.privateip.oc1..example"
    state: present

- name: Delete a public IP
  oracle.oci.oci_public_ip:
    public_ip_id: "ocid1.publicip.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The public IP resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.publicip.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-reserved-ip"
        ip_address: "129.213.100.10"
        lifetime: "RESERVED"
        lifecycle_state: "AVAILABLE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_TERMINATED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    from oci.core import VirtualNetworkClient
    from oci.core.models import CreatePublicIpDetails, UpdatePublicIpDetails
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciPublicIp(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        public_ip_id = self.module.params.get("public_ip_id")
        if not public_ip_id:
            return None
        try:
            return self.client.get_public_ip(public_ip_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreatePublicIpDetails(
            compartment_id=self.module.params["compartment_id"],
            lifetime=self.module.params["lifetime"],
            display_name=self.module.params.get("display_name"),
            private_ip_id=self.module.params.get("private_ip_id"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        public_ip = self.client.create_public_ip(details).data
        return wait_for_resource(
            self.module,
            self.client.get_public_ip,
            public_ip.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def update_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        kwargs = {}
        if self.module.params.get("display_name") is not None:
            kwargs["display_name"] = self.module.params["display_name"]
        if self.module.params.get("private_ip_id") is not None:
            kwargs["private_ip_id"] = self.module.params["private_ip_id"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdatePublicIpDetails(**kwargs)
        self.client.update_public_ip(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_public_ip,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_public_ip(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_public_ip,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "private_ip_id"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        public_ip_id=dict(type="str"),
        lifetime=dict(type="str", choices=["RESERVED", "EPHEMERAL"]),
        display_name=dict(type="str"),
        private_ip_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "lifetime"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_pub_ip = OciPublicIp(module)
    oci_pub_ip.run()


if __name__ == "__main__":
    main()
