# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Cloud Guard targets."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_cloud_guard
short_description: Manage OCI Cloud Guard targets
description:
  - Create, update, and delete Cloud Guard targets in OCI.
  - Cloud Guard targets define the scope of resources to monitor for security threats.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the target resides.
      - Required when creating a new target.
    type: str
  display_name:
    description:
      - A user-friendly name for the Cloud Guard target.
      - Required when creating a new target.
    type: str
  target_resource_type:
    description:
      - The type of resource being protected by the target.
    type: str
    choices: [COMPARTMENT]
    default: COMPARTMENT
  target_resource_id:
    description:
      - The OCID of the resource being protected (e.g., compartment OCID).
      - Required when creating a new target.
    type: str
  target_detector_recipes:
    description:
      - List of detector recipe configurations for the target.
      - Each item should contain a C(detector_recipe_id) key.
    type: list
    elements: dict
  target_responder_recipes:
    description:
      - List of responder recipe configurations for the target.
      - Each item should contain a C(responder_recipe_id) key.
    type: list
    elements: dict
  target_id:
    description:
      - The OCID of the Cloud Guard target.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the target.
    type: str
    choices: [present, absent]
    default: present
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a Cloud Guard target for a compartment
  stevefulme1.oci_cloud.oci_cloud_guard:
    compartment_id: ocid1.compartment.oc1..example
    display_name: my-cg-target
    target_resource_type: COMPARTMENT
    target_resource_id: ocid1.compartment.oc1..example
    target_detector_recipes:
      - detector_recipe_id: ocid1.cloudguarddetectorrecipe.oc1..example
    target_responder_recipes:
      - responder_recipe_id: ocid1.cloudguardresponderrecipe.oc1..example
    state: present

- name: Update a Cloud Guard target
  stevefulme1.oci_cloud.oci_cloud_guard:
    target_id: ocid1.cloudguardtarget.oc1..example
    display_name: renamed-target
    state: present

- name: Delete a Cloud Guard target
  stevefulme1.oci_cloud.oci_cloud_guard:
    target_id: ocid1.cloudguardtarget.oc1..example
    state: absent
"""

RETURN = r"""
resource:
  description: The Cloud Guard target resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the target.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the target.
      type: str
    target_resource_type:
      description: The type of resource being protected.
      type: str
    target_resource_id:
      description: The OCID of the protected resource.
      type: str
    lifecycle_state:
      description: The current lifecycle state of the target.
      type: str
    time_created:
      description: The date and time the target was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import (
    create_service_client,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.cloud_guard import CloudGuardClient
    from oci.cloud_guard.models import (
        CreateTargetDetails,
        UpdateTargetDetails,
        TargetDetectorRecipeDetails,
        TargetResponderRecipeDetails,
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


def get_target(client, target_id):
    """Get a Cloud Guard target by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_target, target_id)
        target = response.data
        if target.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return target
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_target(client, compartment_id, display_name):
    """Find a target by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    targets = call_with_retry(client.list_targets, compartment_id).data
    for t in targets.items if hasattr(targets, "items") else targets:
        if t.display_name == display_name and t.lifecycle_state not in (
            "DELETED",
            "TERMINATED",
        ):
            return get_target(client, t.id)
    return None


def build_detector_recipes(recipe_list):
    """Build detector recipe details from parameter list."""
    if not recipe_list:
        return None
    recipes = []
    for item in recipe_list:
        recipes.append(
            TargetDetectorRecipeDetails(
                detector_recipe_id=item["detector_recipe_id"],
            )
        )
    return recipes


def build_responder_recipes(recipe_list):
    """Build responder recipe details from parameter list."""
    if not recipe_list:
        return None
    recipes = []
    for item in recipe_list:
        recipes.append(
            TargetResponderRecipeDetails(
                responder_recipe_id=item["responder_recipe_id"],
            )
        )
    return recipes


def create_target(module, client):
    """Create a new Cloud Guard target."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        target_resource_type=module.params.get("target_resource_type", "COMPARTMENT"),
        target_resource_id=module.params["target_resource_id"],
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )

    detector_recipes = build_detector_recipes(module.params.get("target_detector_recipes"))
    if detector_recipes:
        kwargs["target_detector_recipes"] = detector_recipes

    responder_recipes = build_responder_recipes(module.params.get("target_responder_recipes"))
    if responder_recipes:
        kwargs["target_responder_recipes"] = responder_recipes

    details = CreateTargetDetails(**kwargs)
    response = call_with_retry(client.create_target, details)
    target = response.data

    if module.params.get("wait", True):
        target = wait_for_resource(
            module,
            client.get_target,
            target.id,
            target_states={"ACTIVE"},
        )
    return target


def update_target(module, client, target):
    """Update an existing Cloud Guard target."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return target

    details = UpdateTargetDetails(**kwargs)
    response = call_with_retry(client.update_target, target.id, details)
    return response.data


def delete_target(module, client, target):
    """Delete a Cloud Guard target."""
    call_with_retry(client.delete_target, target.id)

    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_target,
            target.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, target):
    """Check if target needs to be updated."""
    if module.params.get("display_name") and target.display_name != module.params["display_name"]:
        return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(target, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(target, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        target_resource_type=dict(type="str", choices=["COMPARTMENT"], default="COMPARTMENT"),
        target_resource_id=dict(type="str"),
        target_detector_recipes=dict(type="list", elements="dict"),
        target_responder_recipes=dict(type="list", elements="dict"),
        target_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "target_resource_id"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, CloudGuardClient)
    state = module.params.get("state", "present")
    target_id = module.params.get("target_id")

    # Get existing resource
    target = None
    if target_id:
        target = get_target(client, target_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        target = find_target(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if target is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_target(module, client, target)
        module.exit_json(changed=True)
        return

    # state == present
    if target is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(
                msg="compartment_id, display_name, and target_resource_id are required to create a target."
            )
        if module.check_mode:
            module.exit_json(changed=True)
        target = create_target(module, client)
        module.exit_json(changed=True, resource=to_dict(target))
        return

    if needs_update(module, target):
        if module.check_mode:
            module.exit_json(changed=True)
        target = update_target(module, client, target)
        module.exit_json(changed=True, resource=to_dict(target))
        return

    module.exit_json(changed=False, resource=to_dict(target))


def main():
    run_module()


if __name__ == "__main__":
    main()
