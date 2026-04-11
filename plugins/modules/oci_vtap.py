# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Virtual Test Access Points (VTAPs)."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_vtap
short_description: Manage Virtual Test Access Points (VTAPs) in OCI
description:
    - Create, update, and delete Virtual Test Access Points in Oracle Cloud Infrastructure.
    - VTAPs provide traffic mirroring for network monitoring and troubleshooting.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the VTAP.
            - Required for creating a VTAP.
        type: str
    vtap_id:
        description:
            - The OCID of the VTAP.
            - Required for update and delete operations.
        type: str
    vcn_id:
        description:
            - The OCID of the VCN containing the VTAP.
            - Required for creating a VTAP.
        type: str
    display_name:
        description:
            - A user-friendly name for the VTAP.
        type: str
    source_id:
        description:
            - The OCID of the source resource for mirroring traffic.
            - Required for creating a VTAP.
        type: str
    target_id:
        description:
            - The OCID of the destination resource for mirrored traffic.
            - Required for creating a VTAP.
        type: str
    capture_filter_id:
        description:
            - The OCID of the capture filter to apply to the VTAP.
            - Required for creating a VTAP.
        type: str
    is_vtap_enabled:
        description:
            - Whether the VTAP is enabled.
        type: bool
    state:
        description:
            - The desired state of the VTAP.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a VTAP
  oracle.oci.oci_vtap:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "ocid1.vcn.oc1..example"
    source_id: "ocid1.vnic.oc1..example"
    target_id: "ocid1.networkloadbalancer.oc1..example"
    capture_filter_id: "ocid1.capturefilter.oc1..example"
    display_name: "my-vtap"
    is_vtap_enabled: true
    state: present

- name: Update a VTAP
  oracle.oci.oci_vtap:
    vtap_id: "ocid1.vtap.oc1..example"
    display_name: "updated-vtap"
    is_vtap_enabled: false
    state: present

- name: Delete a VTAP
  oracle.oci.oci_vtap:
    vtap_id: "ocid1.vtap.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The VTAP resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.vtap.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        vcn_id: "ocid1.vcn.oc1..example"
        display_name: "my-vtap"
        source_id: "ocid1.vnic.oc1..example"
        target_id: "ocid1.networkloadbalancer.oc1..example"
        capture_filter_id: "ocid1.capturefilter.oc1..example"
        is_vtap_enabled: true
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
    from oci.core.models import (
        CreateVtapDetails,
        UpdateVtapDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVtap(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        vtap_id = self.module.params.get("vtap_id")
        if not vtap_id:
            return None
        try:
            return self.client.get_vtap(vtap_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateVtapDetails(
            compartment_id=self.module.params["compartment_id"],
            vcn_id=self.module.params["vcn_id"],
            source_id=self.module.params["source_id"],
            target_id=self.module.params["target_id"],
            capture_filter_id=self.module.params["capture_filter_id"],
            display_name=self.module.params.get("display_name"),
            is_vtap_enabled=self.module.params.get("is_vtap_enabled"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_vtap(details).data
        return wait_for_resource(
            self.module,
            self.client.get_vtap,
            resource.id,
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
        if self.module.params.get("is_vtap_enabled") is not None:
            kwargs["is_vtap_enabled"] = self.module.params["is_vtap_enabled"]
        if self.module.params.get("source_id") is not None:
            kwargs["source_id"] = self.module.params["source_id"]
        if self.module.params.get("target_id") is not None:
            kwargs["target_id"] = self.module.params["target_id"]
        if self.module.params.get("capture_filter_id") is not None:
            kwargs["capture_filter_id"] = self.module.params["capture_filter_id"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateVtapDetails(**kwargs)
        self.client.update_vtap(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_vtap,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_vtap(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_vtap,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "is_vtap_enabled", "source_id", "target_id", "capture_filter_id"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        vtap_id=dict(type="str"),
        vcn_id=dict(type="str"),
        display_name=dict(type="str"),
        source_id=dict(type="str"),
        target_id=dict(type="str"),
        capture_filter_id=dict(type="str"),
        is_vtap_enabled=dict(type="bool"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "vcn_id", "source_id", "target_id", "capture_filter_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciVtap(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
