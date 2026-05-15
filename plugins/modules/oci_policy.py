# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI IAM policies."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_policy
short_description: Manage OCI IAM policies
description:
    - Create, update, and delete IAM policies in Oracle Cloud Infrastructure.
    - Policies specify who can access which OCI resources and the type of
      access they have.
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    compartment_id:
        description:
            - The OCID of the compartment where the policy will be created.
            - Required when creating a new policy.
        type: str
    name:
        description:
            - The name of the policy. Must be unique within the compartment.
            - Required when creating a new policy.
        type: str
    description:
        description:
            - The description of the policy.
            - Required when creating a new policy.
        type: str
    statements:
        description:
            - A list of policy statements written in the OCI policy language.
            - "Example: C(['Allow group developers to manage all-resources in compartment dev'])"
            - Required when creating a new policy.
        type: list
        elements: str
    policy_id:
        description:
            - The OCID of the policy to update or delete.
            - Required for update and delete operations.
        type: str
    state:
        description:
            - The desired state of the policy.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a policy
  stevefulme1.oci_cloud.oci_policy:
    compartment_id: "ocid1.tenancy.oc1..example"
    name: "dev-policy"
    description: "Allow developers to manage dev compartment"
    statements:
      - "Allow group developers to manage all-resources in compartment dev"
      - "Allow group developers to read all-resources in tenancy"
    state: present

- name: Update policy statements
  stevefulme1.oci_cloud.oci_policy:
    policy_id: "ocid1.policy.oc1..example"
    statements:
      - "Allow group developers to manage all-resources in compartment dev"
    state: present

- name: Delete a policy
  stevefulme1.oci_cloud.oci_policy:
    policy_id: "ocid1.policy.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The policy details.
    returned: on success
    type: dict
    contains:
        id:
            description: The OCID of the policy.
            type: str
        compartment_id:
            description: The OCID of the compartment.
            type: str
        name:
            description: The name of the policy.
            type: str
        description:
            description: The description of the policy.
            type: str
        statements:
            description: The list of policy statements.
            type: list
            elements: str
        lifecycle_state:
            description: The current lifecycle state of the policy.
            type: str
        time_created:
            description: The date and time the policy was created.
            type: str
        freeform_tags:
            description: Free-form tags for this resource.
            type: dict
        defined_tags:
            description: Defined tags for this resource.
            type: dict
"""

try:
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreatePolicyDetails,
        UpdatePolicyDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        statements=dict(type="list", elements="str"),
        policy_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_existing_resource(client, module):
    """Return the existing policy or None."""
    policy_id = module.params.get("policy_id")
    if policy_id:
        try:
            return call_with_retry(client.get_policy, policy_id).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    compartment_id = module.params.get("compartment_id")
    name = module.params.get("name")
    if compartment_id and name:
        policies = call_with_retry(
            client.list_policies,
            compartment_id,
        ).data
        for policy in policies:
            if policy.name == name and policy.lifecycle_state == LIFECYCLE_ACTIVE:
                return policy

    return None


def create_resource(client, module):
    """Create a new policy."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        description=module.params["description"],
        statements=module.params["statements"],
    )
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreatePolicyDetails(**kwargs)
    resource = call_with_retry(client.create_policy, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_policy,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def update_resource(client, module, resource):
    """Update an existing policy."""
    kwargs = {}
    for attr in ("description", "statements"):
        value = module.params.get(attr)
        if value is not None and value != getattr(resource, attr, None):
            kwargs[attr] = value

    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdatePolicyDetails(**kwargs)
    resource = call_with_retry(client.update_policy, resource.id, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            client.get_policy,
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def delete_resource(client, module, resource):
    """Delete a policy."""
    call_with_retry(client.delete_policy, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_policy,
            resource.id,
            target_states={LIFECYCLE_DELETED, "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if any attribute needs updating."""
    for attr in ("description", "statements"):
        desired = module.params.get(attr)
        if desired is not None and desired != getattr(resource, attr, None):
            return True
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        return True
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["policy_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, IdentityClient)
    state = module.params["state"]

    resource = get_existing_resource(client, module)

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(client, module, resource)
        module.exit_json(changed=True)
        return

    # state == present
    if resource is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(client, module)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(module, resource):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(client, module, resource)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(resource))


if __name__ == "__main__":
    main()
