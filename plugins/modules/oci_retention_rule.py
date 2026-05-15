# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Object Storage Retention Rules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_retention_rule
short_description: Manage OCI Object Storage Retention Rules
description:
  - Create, update, and delete retention rules on OCI Object Storage buckets.
  - Retention rules enforce data immutability for compliance requirements.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  namespace_name:
    description:
      - The Object Storage namespace.
    type: str
    required: true
  bucket_name:
    description:
      - The name of the bucket.
    type: str
    required: true
  retention_rule_id:
    description:
      - The ID of the retention rule.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-specified name for the retention rule.
    type: str
  duration:
    description:
      - The duration for the retention rule.
    type: dict
    suboptions:
      time_amount:
        description: The duration amount.
        type: int
        required: true
      time_unit:
        description: The duration time unit.
        type: str
        choices: [DAYS, YEARS]
        required: true
  time_rule_locked:
    description:
      - The date and time after which the rule becomes locked (RFC 3339 format).
      - Once locked, the rule cannot be deleted or modified.
    type: str
  state:
    description:
      - The desired state of the retention rule.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a retention rule for 365 days
  stevefulme1.oci_cloud.oci_retention_rule:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    display_name: "annual-retention"
    duration:
      time_amount: 365
      time_unit: DAYS
    state: present

- name: Create a locked retention rule
  stevefulme1.oci_cloud.oci_retention_rule:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    display_name: "compliance-lock"
    duration:
      time_amount: 7
      time_unit: YEARS
    time_rule_locked: "2027-01-01T00:00:00Z"
    state: present

- name: Delete a retention rule
  stevefulme1.oci_cloud.oci_retention_rule:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    retention_rule_id: "example-retention-rule-id"
    state: absent
"""

RETURN = r"""
resource:
  description: The retention rule details.
  returned: on success
  type: dict
  contains:
    id:
      description: The ID of the retention rule.
      type: str
    display_name:
      description: The display name of the retention rule.
      type: str
    duration:
      description: The duration of the retention rule.
      type: dict
    time_rule_locked:
      description: The date when the rule becomes locked.
      type: str
    time_created:
      description: The date the rule was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.object_storage import ObjectStorageClient
    from oci.object_storage.models import (
        CreateRetentionRuleDetails,
        UpdateRetentionRuleDetails,
        Duration,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_retention_rule(client, namespace_name, bucket_name, retention_rule_id):
    """Get a retention rule by ID, return None if not found."""
    try:
        response = call_with_retry(
            client.get_retention_rule,
            namespace_name,
            bucket_name,
            retention_rule_id,
        )
        return response.data
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_retention_rule(client, namespace_name, bucket_name, display_name):
    """Find a retention rule by display name."""
    if not display_name:
        return None
    rules = call_with_retry(
        client.list_retention_rules,
        namespace_name,
        bucket_name,
    ).data.items
    for r in rules:
        if r.display_name == display_name:
            return get_retention_rule(client, namespace_name, bucket_name, r.id)
    return None


def build_duration(duration_param):
    """Build a Duration object from module params."""
    if not duration_param:
        return None
    return Duration(
        time_amount=duration_param["time_amount"],
        time_unit=duration_param["time_unit"],
    )


def create_retention_rule(module, client):
    """Create a new retention rule."""
    details = CreateRetentionRuleDetails(
        display_name=module.params.get("display_name"),
        duration=build_duration(module.params.get("duration")),
        time_rule_locked=module.params.get("time_rule_locked"),
    )
    response = call_with_retry(
        client.create_retention_rule,
        module.params["namespace_name"],
        module.params["bucket_name"],
        details,
    )
    return response.data


def update_retention_rule(module, client, rule):
    """Update an existing retention rule."""
    rule_id = module.params.get("retention_rule_id") or rule.id
    details = UpdateRetentionRuleDetails(
        display_name=module.params.get("display_name") or rule.display_name,
        duration=build_duration(module.params.get("duration")),
        time_rule_locked=module.params.get("time_rule_locked"),
    )
    response = call_with_retry(
        client.update_retention_rule,
        module.params["namespace_name"],
        module.params["bucket_name"],
        rule_id,
        details,
    )
    return response.data


def delete_retention_rule(module, client, rule):
    """Delete a retention rule."""
    rule_id = module.params.get("retention_rule_id") or rule.id
    call_with_retry(
        client.delete_retention_rule,
        module.params["namespace_name"],
        module.params["bucket_name"],
        rule_id,
    )


def needs_update(module, rule):
    """Check if the retention rule needs updating."""
    if module.params.get("display_name") and module.params["display_name"] != rule.display_name:
        return True
    duration_param = module.params.get("duration")
    if duration_param and rule.duration:
        if (duration_param["time_amount"] != rule.duration.time_amount
                or duration_param["time_unit"] != rule.duration.time_unit):
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        namespace_name=dict(type="str", required=True),
        bucket_name=dict(type="str", required=True),
        retention_rule_id=dict(type="str"),
        display_name=dict(type="str"),
        duration=dict(type="dict"),
        time_rule_locked=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ObjectStorageClient)
    state = module.params.get("state", "present")
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]
    retention_rule_id = module.params.get("retention_rule_id")

    # Get existing resource
    rule = None
    if retention_rule_id:
        rule = get_retention_rule(client, namespace_name, bucket_name, retention_rule_id)
    elif module.params.get("display_name"):
        rule = find_retention_rule(client, namespace_name, bucket_name, module.params["display_name"])

    if state == "absent":
        if rule is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_retention_rule(module, client, rule)
        module.exit_json(changed=True)
        return

    # state == present
    if rule is None:
        if module.check_mode:
            module.exit_json(changed=True)
        rule = create_retention_rule(module, client)
        module.exit_json(changed=True, resource=to_dict(rule))
        return

    if needs_update(module, rule):
        if module.check_mode:
            module.exit_json(changed=True)
        rule = update_retention_rule(module, client, rule)
        module.exit_json(changed=True, resource=to_dict(rule))
        return

    module.exit_json(changed=False, resource=to_dict(rule))


def main():
    run_module()


if __name__ == "__main__":
    main()
