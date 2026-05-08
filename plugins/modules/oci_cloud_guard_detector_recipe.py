# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Cloud Guard detector recipes."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_cloud_guard_detector_recipe
short_description: Manage OCI Cloud Guard detector recipes
description:
  - Create, update, and delete Cloud Guard detector recipes in Oracle Cloud Infrastructure.
  - Detector recipes define the rules used to identify security threats and misconfigurations.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the detector recipe resides.
      - Required when creating a new detector recipe.
    type: str
  detector_recipe_id:
    description:
      - The OCID of the detector recipe.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the detector recipe.
      - Required when creating a new detector recipe.
    type: str
  detector:
    description:
      - The type of detector.
    type: str
    choices: [IAAS_ACTIVITY_DETECTOR, IAAS_CONFIGURATION_DETECTOR, IAAS_THREAT_DETECTOR, IAAS_LOG_INSIGHT_DETECTOR]
  source_detector_recipe_id:
    description:
      - The OCID of the source detector recipe to clone from.
      - Required when creating a new detector recipe.
    type: str
  detector_rules:
    description:
      - List of detector rule overrides.
      - Each item should contain C(detector_rule_id) and C(details) keys.
    type: list
    elements: dict
  state:
    description:
      - The desired state of the detector recipe.
    type: str
    choices: [present, absent]
    default: present
extends_documentation_fragment:
  - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = r"""
- name: Create a detector recipe
  stevefulme1.oci_cloud.oci_cloud_guard_detector_recipe:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "custom-detector-recipe"
    source_detector_recipe_id: "ocid1.cloudguarddetectorrecipe.oc1..example"
    state: present

- name: Update a detector recipe
  stevefulme1.oci_cloud.oci_cloud_guard_detector_recipe:
    detector_recipe_id: "ocid1.cloudguarddetectorrecipe.oc1..example"
    display_name: "renamed-detector-recipe"
    state: present

- name: Delete a detector recipe
  stevefulme1.oci_cloud.oci_cloud_guard_detector_recipe:
    detector_recipe_id: "ocid1.cloudguarddetectorrecipe.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The detector recipe details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the detector recipe.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the detector recipe.
      type: str
    detector:
      description: The type of detector.
      type: str
    source_detector_recipe_id:
      description: The OCID of the source detector recipe.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    time_created:
      description: The date and time the recipe was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.cloud_guard import CloudGuardClient
    from oci.cloud_guard.models import (
        CreateDetectorRecipeDetails,
        UpdateDetectorRecipeDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_resource(client, resource_id):
    """Get a detector recipe by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_detector_recipe, resource_id)
        resource = response.data
        if resource.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return resource
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, compartment_id, display_name):
    """Find a detector recipe by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    resources = call_with_retry(
        client.list_detector_recipes, compartment_id=compartment_id
    ).data
    items = resources.items if hasattr(resources, "items") else resources
    for r in items:
        if r.display_name == display_name and r.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_resource(client, r.id)
    return None


def create_resource(module, client):
    """Create a new detector recipe."""
    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        source_detector_recipe_id=module.params["source_detector_recipe_id"],
    )
    if module.params.get("detector"):
        kwargs["detector"] = module.params["detector"]
    if module.params.get("detector_rules"):
        kwargs["detector_rules"] = module.params["detector_rules"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateDetectorRecipeDetails(**kwargs)
    response = call_with_retry(client.create_detector_recipe, details)
    resource = response.data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module, client.get_detector_recipe, resource.id,
            target_states={"ACTIVE"},
        )
    return resource


def update_resource(module, client, resource):
    """Update an existing detector recipe."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        if module.params["display_name"] != getattr(resource, "display_name", None):
            kwargs["display_name"] = module.params["display_name"]
    if module.params.get("detector_rules") is not None:
        kwargs["detector_rules"] = module.params["detector_rules"]
    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateDetectorRecipeDetails(**kwargs)
    response = call_with_retry(client.update_detector_recipe, resource.id, details)
    return response.data


def delete_resource(module, client, resource):
    """Delete a detector recipe."""
    call_with_retry(client.delete_detector_recipe, resource.id)
    if module.params.get("wait", True):
        wait_for_resource(
            module, client.get_detector_recipe, resource.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if the detector recipe needs updating."""
    if module.params.get("display_name") is not None:
        if module.params["display_name"] != getattr(resource, "display_name", None):
            return True
    if module.params.get("detector_rules") is not None:
        return True
    freeform_tags = module.params.get("freeform_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        return True
    defined_tags = module.params.get("defined_tags")
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        return True
    return False


def main():
    module_args = dict(
        compartment_id=dict(type="str"),
        detector_recipe_id=dict(type="str"),
        display_name=dict(type="str"),
        detector=dict(
            type="str",
            choices=[
                "IAAS_ACTIVITY_DETECTOR",
                "IAAS_CONFIGURATION_DETECTOR",
                "IAAS_THREAT_DETECTOR",
                "IAAS_LOG_INSIGHT_DETECTOR",
            ],
        ),
        source_detector_recipe_id=dict(type="str"),
        detector_rules=dict(type="list", elements="dict"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["detector_recipe_id"]),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, CloudGuardClient)
    state = module.params["state"]
    resource_id = module.params.get("detector_recipe_id")

    resource = None
    if resource_id:
        resource = get_resource(client, resource_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        resource = find_resource(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if resource is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, resource)
        module.exit_json(changed=True)
        return

    if resource is None:
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    if needs_update(module, resource):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, resource)
        module.exit_json(changed=True, resource=to_dict(resource))
        return

    module.exit_json(changed=False, resource=to_dict(resource))


if __name__ == "__main__":
    main()
