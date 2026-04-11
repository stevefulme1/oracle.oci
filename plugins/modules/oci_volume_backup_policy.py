# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Volume Backup Policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_volume_backup_policy
short_description: Manage OCI Volume Backup Policies
description:
    - Create, update, and delete scheduled volume backup policies in Oracle
      Cloud Infrastructure.
    - Uses the BlockstorageClient from the OCI Python SDK.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment to contain the backup policy.
            - Required when creating a new policy.
        type: str
    policy_id:
        description:
            - The OCID of the volume backup policy.
            - Required for update and delete operations.
        type: str
    display_name:
        description:
            - A user-friendly name for the backup policy.
        type: str
    schedules:
        description:
            - Schedules for the backup policy.
        type: list
        elements: dict
        suboptions:
            backup_type:
                description:
                    - The type of backup to create (FULL or INCREMENTAL).
                type: str
                required: true
                choices: [FULL, INCREMENTAL]
            period:
                description:
                    - How often the backup should occur (ONE_DAY, ONE_WEEK, ONE_MONTH, ONE_YEAR).
                type: str
                required: true
                choices: [ONE_DAY, ONE_WEEK, ONE_MONTH, ONE_YEAR]
            retention_seconds:
                description:
                    - How long the backup should be kept, in seconds.
                type: int
                required: true
            hour_of_day:
                description:
                    - The hour of the day to create the backup (0-23).
                type: int
            day_of_week:
                description:
                    - The day of the week to create the backup.
                type: str
                choices: [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
            day_of_month:
                description:
                    - The day of the month to create the backup (1-31).
                type: int
            month:
                description:
                    - The month of the year to create the backup.
                type: str
            offset_seconds:
                description:
                    - The number of seconds to offset the schedule from the base time.
                type: int
            offset_type:
                description:
                    - How the offset is calculated (STRUCTURED or NUMERIC_SECONDS).
                type: str
                choices: [STRUCTURED, NUMERIC_SECONDS]
            time_zone:
                description:
                    - The time zone for the schedule (REGIONAL_DATA_CENTER_TIME or UTC).
                type: str
                default: UTC
                choices: [REGIONAL_DATA_CENTER_TIME, UTC]
    state:
        description:
            - The desired state of the backup policy.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a daily backup policy
  oracle.oci.oci_volume_backup_policy:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "daily-backup-policy"
    schedules:
      - backup_type: INCREMENTAL
        period: ONE_DAY
        retention_seconds: 604800
        hour_of_day: 2
        time_zone: UTC
    state: present

- name: Update a backup policy
  oracle.oci.oci_volume_backup_policy:
    policy_id: "ocid1.volumebackuppolicy.oc1..example"
    display_name: "updated-backup-policy"
    schedules:
      - backup_type: FULL
        period: ONE_WEEK
        retention_seconds: 2592000
        hour_of_day: 3
        day_of_week: SUNDAY
    state: present

- name: Delete a backup policy
  oracle.oci.oci_volume_backup_policy:
    policy_id: "ocid1.volumebackuppolicy.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: Details of the volume backup policy.
    returned: on success
    type: dict
    sample:
        id: "ocid1.volumebackuppolicy.oc1..example"
        display_name: "daily-backup-policy"
        schedules:
            - backup_type: "INCREMENTAL"
              period: "ONE_DAY"
              retention_seconds: 604800
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_resource import OciResourceBase

try:
    import oci
    from oci.core import BlockstorageClient
    from oci.core.models import (
        CreateVolumeBackupPolicyDetails,
        UpdateVolumeBackupPolicyDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


class OciVolumeBackupPolicy(OciResourceBase):
    """Manage OCI Volume Backup Policies."""

    client_class = BlockstorageClient if HAS_OCI_SDK else None

    def get_resource(self):
        policy_id = self.module.params.get("policy_id")
        if not policy_id:
            return None
        try:
            return call_with_retry(
                self.client.get_volume_backup_policy, policy_id
            ).data
        except oci.exceptions.ServiceError as e:
            if e.status == 404:
                return None
            raise

    def create_resource(self):
        freeform_tags, defined_tags = self.get_tags()
        details = CreateVolumeBackupPolicyDetails(
            compartment_id=self.module.params["compartment_id"],
            display_name=self.module.params.get("display_name"),
            schedules=self.module.params.get("schedules"),
            freeform_tags=freeform_tags,
            defined_tags=defined_tags,
        )
        response = call_with_retry(
            self.client.create_volume_backup_policy, details
        )
        return response.data

    def update_resource(self, resource):
        freeform_tags, defined_tags = self.get_tags()
        details = UpdateVolumeBackupPolicyDetails(
            display_name=self.module.params.get("display_name") or resource.display_name,
            schedules=self.module.params.get("schedules"),
            freeform_tags=freeform_tags if freeform_tags is not None else resource.freeform_tags,
            defined_tags=defined_tags if defined_tags is not None else resource.defined_tags,
        )
        call_with_retry(
            self.client.update_volume_backup_policy, resource.id, details
        )
        return call_with_retry(
            self.client.get_volume_backup_policy, resource.id
        ).data

    def delete_resource(self, resource):
        call_with_retry(
            self.client.delete_volume_backup_policy, resource.id
        )

    def _updatable_attributes(self):
        return ["display_name", "schedules"]


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        policy_id=dict(type="str"),
        display_name=dict(type="str"),
        schedules=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id",), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    resource_helper = OciVolumeBackupPolicy(module)
    resource_helper.run()


if __name__ == "__main__":
    main()
