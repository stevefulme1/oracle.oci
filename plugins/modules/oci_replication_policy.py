# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Object Storage Replication Policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_replication_policy
short_description: Manage OCI Object Storage Replication Policies
description:
  - Create and delete replication policies for OCI Object Storage buckets.
  - Replication policies enable cross-region replication of objects.
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
  replication_policy_id:
    description:
      - The ID of the replication policy.
      - Required for delete operations.
    type: str
  name:
    description:
      - A user-specified name for the replication policy.
      - Required when creating.
    type: str
  destination_region_name:
    description:
      - The destination region to replicate to.
      - Required when creating.
    type: str
  destination_bucket_name:
    description:
      - The name of the destination bucket.
      - Required when creating.
    type: str
  state:
    description:
      - The desired state of the replication policy.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a replication policy
  stevefulme1.oci_cloud.oci_replication_policy:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    name: "replicate-to-phoenix"
    destination_region_name: "us-phoenix-1"
    destination_bucket_name: "my-bucket-replica"
    state: present

- name: Delete a replication policy
  stevefulme1.oci_cloud.oci_replication_policy:
    namespace_name: "mynamespace"
    bucket_name: "my-bucket"
    replication_policy_id: "example-replication-id"
    state: absent
"""

RETURN = r"""
resource:
  description: The replication policy details.
  returned: on success
  type: dict
  contains:
    id:
      description: The ID of the replication policy.
      type: str
    name:
      description: The name of the replication policy.
      type: str
    destination_region_name:
      description: The destination region.
      type: str
    destination_bucket_name:
      description: The destination bucket name.
      type: str
    status:
      description: The replication status.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.object_storage import ObjectStorageClient
    from oci.object_storage.models import CreateReplicationPolicyDetails
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


def get_replication_policy(client, namespace_name, bucket_name, replication_policy_id):
    """Get a replication policy by ID, return None if not found."""
    try:
        response = call_with_retry(
            client.get_replication_policy,
            namespace_name,
            bucket_name,
            replication_policy_id,
        )
        return response.data
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_replication_policy(client, namespace_name, bucket_name, name):
    """Find a replication policy by name."""
    if not name:
        return None
    policies = call_with_retry(
        client.list_replication_policies,
        namespace_name,
        bucket_name,
    ).data
    for p in policies:
        if p.name == name:
            return get_replication_policy(client, namespace_name, bucket_name, p.id)
    return None


def create_replication_policy(module, client):
    """Create a new replication policy."""
    details = CreateReplicationPolicyDetails(
        name=module.params["name"],
        destination_region_name=module.params["destination_region_name"],
        destination_bucket_name=module.params["destination_bucket_name"],
    )
    response = call_with_retry(
        client.create_replication_policy,
        module.params["namespace_name"],
        module.params["bucket_name"],
        details,
    )
    return response.data


def delete_replication_policy(module, client, policy):
    """Delete a replication policy."""
    policy_id = module.params.get("replication_policy_id") or policy.id
    call_with_retry(
        client.delete_replication_policy,
        module.params["namespace_name"],
        module.params["bucket_name"],
        policy_id,
    )


def run_module():
    """Main module execution."""
    module_args = dict(
        namespace_name=dict(type="str", required=True),
        bucket_name=dict(type="str", required=True),
        replication_policy_id=dict(type="str"),
        name=dict(type="str"),
        destination_region_name=dict(type="str"),
        destination_bucket_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("name", "destination_region_name", "destination_bucket_name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ObjectStorageClient)
    state = module.params.get("state", "present")
    namespace_name = module.params["namespace_name"]
    bucket_name = module.params["bucket_name"]
    replication_policy_id = module.params.get("replication_policy_id")

    # Get existing resource
    policy = None
    if replication_policy_id:
        policy = get_replication_policy(client, namespace_name, bucket_name, replication_policy_id)
    elif module.params.get("name"):
        policy = find_replication_policy(client, namespace_name, bucket_name, module.params["name"])

    if state == "absent":
        if policy is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_replication_policy(module, client, policy)
        module.exit_json(changed=True)
        return

    # state == present: create only (replication policies cannot be updated)
    if policy is not None:
        module.exit_json(changed=False, resource=to_dict(policy))
        return

    if module.check_mode:
        module.exit_json(changed=True)
    policy = create_replication_policy(module, client)
    module.exit_json(changed=True, resource=to_dict(policy))


def main():
    run_module()


if __name__ == "__main__":
    main()
