# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Instance Console History."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_instance_console_history
short_description: Manage OCI Instance Console History
description:
    - Capture and delete instance console history in Oracle Cloud Infrastructure.
    - Uses the ComputeClient from the OCI Python SDK.
    - This is a create-only resource; update is not supported.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment containing the instance.
        type: str
    console_history_id:
        description:
            - The OCID of the console history.
            - Required for delete operations.
        type: str
    instance_id:
        description:
            - The OCID of the instance to capture console history for.
            - Required when creating a new console history capture.
        type: str
    display_name:
        description:
            - A user-friendly name for the console history.
        type: str
    state:
        description:
            - The desired state of the console history.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Capture console history for an instance
  stevefulme1.oci_cloud.oci_instance_console_history:
    instance_id: "ocid1.instance.oc1..example"
    display_name: "my-console-history"
    state: present

- name: Delete a console history
  stevefulme1.oci_cloud.oci_instance_console_history:
    console_history_id: "ocid1.consolehistory.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the console history.
    returned: on success
    type: dict
    sample:
        id: "ocid1.consolehistory.oc1..example"
        instance_id: "ocid1.instance.oc1..example"
        display_name: "my-console-history"
        lifecycle_state: "SUCCEEDED"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    READY_STATES,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import ComputeClient
    from oci.core.models import CaptureConsoleHistoryDetails
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciInstanceConsoleHistory(OciResourceBase):
    """Manage OCI Instance Console History."""

    client_class = ComputeClient if HAS_OCI_SDK else None

    def get_resource(self):
        history_id = self.module.params.get("console_history_id")
        if not history_id:
            return None
        try:
            return call_with_retry(
                self.client.get_console_history, history_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CaptureConsoleHistoryDetails(
            instance_id=self.module.params["instance_id"],
            display_name=self.module.params.get("display_name"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(
            self.client.capture_console_history, details
        )
        return wait_for_resource(
            self.module,
            self.client.get_console_history,
            response.data.id,
            READY_STATES | {"SUCCEEDED"},
        )

    def update_resource(self, resource):
        # Console history does not support updates.
        return resource

    def delete_resource(self, resource):
        call_with_retry(self.client.delete_console_history, resource.id)

    def _updatable_attributes(self):
        return []


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        console_history_id=dict(type="str"),
        instance_id=dict(type="str"),
        display_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("instance_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciInstanceConsoleHistory(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
