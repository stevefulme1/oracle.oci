# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Capture Filters."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_capture_filter
short_description: Manage VTAP Capture Filters in OCI
description:
    - Create, update, and delete VTAP Capture Filters in Oracle Cloud Infrastructure.
    - Capture filters define which traffic a VTAP mirrors.
    - Uses the OCI Python SDK VirtualNetworkClient.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the capture filter.
            - Required for creating a capture filter.
        type: str
    capture_filter_id:
        description:
            - The OCID of the capture filter.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the capture filter.
        type: str
    filter_type:
        description:
            - The type of capture filter.
            - Required for creating a capture filter.
        type: str
        choices: [VTAP]
    vtap_capture_filter_rules:
        description:
            - List of rules for filtering VTAP-captured traffic.
            - Each rule is a dict with keys such as traffic_direction, rule_action, and optional protocol/port filters.
        type: list
        elements: dict
    state:
        description:
            - The desired state of the capture filter.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a Capture Filter
  oracle.oci.oci_capture_filter:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-capture-filter"
    filter_type: VTAP
    vtap_capture_filter_rules:
      - traffic_direction: INGRESS
        rule_action: INCLUDE
    state: present

- name: Update a Capture Filter
  oracle.oci.oci_capture_filter:
    capture_filter_id: "ocid1.capturefilter.oc1..example"
    display_name: "updated-filter"
    state: present

- name: Delete a Capture Filter
  oracle.oci.oci_capture_filter:
    capture_filter_id: "ocid1.capturefilter.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The Capture Filter resource.
    returned: on success
    type: dict
    sample:
        id: "ocid1.capturefilter.oc1..example"
        compartment_id: "ocid1.compartment.oc1..example"
        display_name: "my-capture-filter"
        filter_type: "VTAP"
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
        CreateCaptureFilterDetails,
        UpdateCaptureFilterDetails,
    )
    from oci.exceptions import ServiceError
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciCaptureFilter(OciResourceBase):
    def __init__(self, module):
        self.client_class = VirtualNetworkClient
        super().__init__(module)

    def get_resource(self):
        capture_filter_id = self.module.params.get("capture_filter_id")
        if not capture_filter_id:
            return None
        try:
            return self.client.get_capture_filter(capture_filter_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        freeform_tags, defined_tags = self.get_tags()
        details = CreateCaptureFilterDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            filter_type=self.module.params["filter_type"],
            vtap_capture_filter_rules=self.module.params.get("vtap_capture_filter_rules"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        resource = self.client.create_capture_filter(details).data
        return wait_for_resource(
            self.module,
            self.client.get_capture_filter,
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
        if self.module.params.get("vtap_capture_filter_rules") is not None:
            kwargs["vtap_capture_filter_rules"] = self.module.params["vtap_capture_filter_rules"]
        if freeform_tags is not None:
            kwargs["freeform_tags"] = freeform_tags
        if defined_tags is not None:
            kwargs["defined_tags"] = defined_tags

        details = UpdateCaptureFilterDetails(**kwargs)
        self.client.update_capture_filter(resource.id, details)
        return wait_for_resource(
            self.module,
            self.client.get_capture_filter,
            resource.id,
            target_states={LIFECYCLE_AVAILABLE},
        )

    def delete_resource(self, resource):
        from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
            wait_for_resource,
        )

        self.client.delete_capture_filter(resource.id)
        if self.module.params.get("wait", True):
            wait_for_resource(
                self.module,
                self.client.get_capture_filter,
                resource.id,
                target_states={LIFECYCLE_TERMINATED, "DELETED"},
            )

    def _updatable_attributes(self):
        return ["display_name", "vtap_capture_filter_rules"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        capture_filter_id=dict(type="str"),
        display_name=dict(type="str"),
        filter_type=dict(type="str", choices=["VTAP"]),
        vtap_capture_filter_rules=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "filter_type"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    oci_resource = OciCaptureFilter(module)
    oci_resource.run()


if __name__ == "__main__":
    main()
