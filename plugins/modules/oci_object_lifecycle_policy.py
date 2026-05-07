# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Object Storage Lifecycle Policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_object_lifecycle_policy
short_description: Manage OCI Object Storage Lifecycle Policies
description:
  - Put and delete lifecycle policies on OCI Object Storage buckets.
  - Lifecycle policies automate the transition and deletion of objects based on rules.
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
  items:
    description:
      - The list of lifecycle rules for the policy.
      - Required when state is present.
    type: list
    elements: dict
    suboptions:
      name:
        description: A name for the lifecycle rule.
        type: str
        required: true
      action:
        description: The action of the lifecycle rule (e.g., ARCHIVE, INFREQUENT_ACCESS, DELETE, ABORT).
        type: str
        required: true
      time_amount:
        description: The number of time units for the rule.
        type: int
        required: true
      time_unit:
        description: The unit of time for the rule.
        type: str
        choices: [DAYS, YEARS]
        required: true
      target:
        description: The target of the lifecycle rule (objects, multipart-uploads).
        type: str
        default: objects
      is_enabled:
        description: Whether the rule is enabled.
        type: bool
        default: true
      object_name_filter:
        description: Filter for object names.
        type: dict
  state:
    description:
      - The desired state of the lifecycle policy.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Set a lifecycle policy to archive objects after 30 days
  stevefulme1.oci_cloud.oci_object_lifecycle_policy:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    items:
      - name: archive-rule
        action: ARCHIVE
        time_amount: 30
        time_unit: DAYS
        target: objects
        is_enabled: true
    state: present

- name: Delete lifecycle policy
  stevefulme1.oci_cloud.oci_object_lifecycle_policy:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    state: absent
"""

RETURN = r"""
resource:
  description: The lifecycle policy details.
  returned: on success
  type: dict
  contains:
    items:
      description: The list of lifecycle rules.
      type: list
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.object_storage import ObjectStorageClient
    from oci.object_storage.models import (
        PutObjectLifecyclePolicyDetails,
        ObjectLifecycleRule,
        ObjectNameFilter,
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


def get_lifecycle_policy(client, namespace_name, bucket_name):
    """Get the lifecycle policy for a bucket, return None if not found."""
    try:
        response = call_with_retry(
            client.get_object_lifecycle_policy,
            namespace_name,
            bucket_name,
        )
        policy = response.data
        if policy and policy.items:
            return policy
        return None
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def build_rules(items):
    """Build ObjectLifecycleRule list from module params."""
    rules = []
    for item in items:
        name_filter = None
        if item.get("object_name_filter"):
            name_filter = ObjectNameFilter(
                inclusion_prefixes=item["object_name_filter"].get("inclusion_prefixes"),
                inclusion_patterns=item["object_name_filter"].get("inclusion_patterns"),
                exclusion_patterns=item["object_name_filter"].get("exclusion_patterns"),
            )
        rule = ObjectLifecycleRule(
            name=item["name"],
            action=item["action"],
            time_amount=item["time_amount"],
            time_unit=item["time_unit"],
            target=item.get("target", "objects"),
            is_enabled=item.get("is_enabled", True),
            object_name_filter=name_filter,
        )
        rules.append(rule)
    return rules


def put_lifecycle_policy(module, client):
    """Put (create/replace) the lifecycle policy."""
    rules = build_rules(module.params["items"])
    details = PutObjectLifecyclePolicyDetails(items=rules)
    response = call_with_retry(
        client.put_object_lifecycle_policy,
        module.params["namespace_name"],
        module.params["bucket_name"],
        details,
    )
    return response.data


def delete_lifecycle_policy(module, client):
    """Delete the lifecycle policy."""
    call_with_retry(
        client.delete_object_lifecycle_policy,
        module.params["namespace_name"],
        module.params["bucket_name"],
    )


def run_module():
    """Main module execution."""
    module_args = dict(
        namespace_name=dict(type="str", required=True),
        bucket_name=dict(type="str", required=True),
        items=dict(type="list", elements="dict"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("items",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ObjectStorageClient)
    state = module.params.get("state", "present")
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]

    policy = get_lifecycle_policy(client, namespace_name, bucket_name)

    if state == "absent":
        if policy is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_lifecycle_policy(module, client)
        module.exit_json(changed=True)
        return

    # state == present: always put (replace) the policy
    if module.check_mode:
        module.exit_json(changed=True)
    policy = put_lifecycle_policy(module, client)
    module.exit_json(changed=True, resource=to_dict(policy))


def main():
    run_module()


if __name__ == "__main__":
    main()
