#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI tag definitions."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_tag
short_description: Manage OCI tag definitions
description:
    - Create, update, and delete tag definitions in Oracle Cloud Infrastructure.
    - Tag definitions belong to a tag namespace and define the key and optional
      allowed values for tags applied to resources.
version_added: "1.0.0"
author: "Oracle (@oracle)"
options:
    tag_namespace_id:
        description:
            - The OCID of the tag namespace that contains the tag definition.
            - Required when creating a new tag definition.
        type: str
    name:
        description:
            - The name of the tag definition. Must be unique within the tag namespace.
            - Required when creating a new tag definition.
        type: str
    description:
        description:
            - The description of the tag definition.
            - Required when creating a new tag definition.
        type: str
    is_cost_tracking:
        description:
            - Whether the tag is a cost-tracking tag.
            - Cost-tracking tags can be used to track costs in the Cost Analysis tool.
        type: bool
    is_retired:
        description:
            - Whether the tag definition is retired.
            - Retired tags cannot be applied to resources.
        type: bool
    validator:
        description:
            - The tag value validator.
            - Use this to restrict allowed values for the tag.
        type: dict
        suboptions:
            validator_type:
                description:
                    - The type of validator. Currently only C(ENUM) is supported.
                type: str
                required: true
                choices: [ENUM, DEFAULT]
            values:
                description:
                    - The list of allowed values for an ENUM validator.
                type: list
                elements: str
    tag_id:
        description:
            - The OCID of the tag definition to update or delete.
            - Required for update and delete operations when I(tag_namespace_id)
              and I(name) are not provided.
        type: str
    state:
        description:
            - The desired state of the tag definition.
        type: str
        default: present
        choices: [present, absent]
extends_documentation_fragment:
    - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create a simple tag definition
  oracle.oci.oci_tag:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    name: "Environment"
    description: "Environment tag (dev, staging, prod)"
    state: present

- name: Create a tag with enum validator
  oracle.oci.oci_tag:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    name: "Environment"
    description: "Environment tag"
    validator:
      validator_type: ENUM
      values:
        - dev
        - staging
        - prod
    state: present

- name: Create a cost-tracking tag
  oracle.oci.oci_tag:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    name: "CostCenter"
    description: "Cost center code"
    is_cost_tracking: true
    state: present

- name: Retire a tag definition
  oracle.oci.oci_tag:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    tag_id: "ocid1.tagdefinition.oc1..example"
    is_retired: true
    state: present

- name: Delete a tag definition
  oracle.oci.oci_tag:
    tag_namespace_id: "ocid1.tagnamespace.oc1..example"
    tag_id: "ocid1.tagdefinition.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
    description: The tag definition details.
    returned: on success
    type: dict
    contains:
        id:
            description: The OCID of the tag definition.
            type: str
        compartment_id:
            description: The OCID of the compartment that contains the tag namespace.
            type: str
        tag_namespace_id:
            description: The OCID of the tag namespace.
            type: str
        tag_namespace_name:
            description: The name of the tag namespace.
            type: str
        name:
            description: The name of the tag definition.
            type: str
        description:
            description: The description of the tag definition.
            type: str
        is_cost_tracking:
            description: Whether the tag is used for cost tracking.
            type: bool
        is_retired:
            description: Whether the tag definition is retired.
            type: bool
        lifecycle_state:
            description: The current lifecycle state of the tag definition.
            type: str
        time_created:
            description: The date and time the tag definition was created.
            type: str
        validator:
            description: The tag value validator.
            type: dict
"""

try:
    from oci.identity import IdentityClient
    from oci.identity.models import (
        CreateTagDetails,
        UpdateTagDetails,
        DefaultTagDefinitionValidator,
        EnumTagDefinitionValidator,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    LIFECYCLE_ACTIVE,
    LIFECYCLE_DELETED,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    module_args = dict(
        tag_namespace_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        is_cost_tracking=dict(type="bool"),
        is_retired=dict(type="bool"),
        validator=dict(
            type="dict",
            options=dict(
                validator_type=dict(type="str", required=True, choices=["ENUM", "DEFAULT"]),
                values=dict(type="list", elements="str"),
            ),
        ),
        tag_id=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def build_validator(validator_param):
    """Build an OCI validator model from the module parameter."""
    if validator_param is None:
        return None

    vtype = validator_param.get("validator_type", "DEFAULT")
    if vtype == "ENUM":
        return EnumTagDefinitionValidator(values=validator_param.get("values", []))
    return DefaultTagDefinitionValidator()


def validator_to_dict(validator):
    """Convert a validator object to a dict for comparison."""
    if validator is None:
        return None
    result = {"validator_type": getattr(validator, "validator_type", "DEFAULT")}
    if hasattr(validator, "values") and validator.values is not None:
        result["values"] = sorted(validator.values)
    return result


def get_existing_resource(client, module):
    """Return the existing tag definition or None."""
    tag_namespace_id = module.params.get("tag_namespace_id")
    tag_id = module.params.get("tag_id")

    if tag_namespace_id and tag_id:
        # The get_tag API uses tag_namespace_id and tag_name, not tag_id directly.
        # But we can list and find by OCID.
        try:
            tags = call_with_retry(client.list_tags, tag_namespace_id).data
            for tag in tags:
                if tag.id == tag_id:
                    return call_with_retry(client.get_tag, tag_namespace_id, tag.name).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    name = module.params.get("name")
    if tag_namespace_id and name:
        try:
            return call_with_retry(client.get_tag, tag_namespace_id, name).data
        except ServiceError as e:
            if e.status == 404:
                return None
            raise

    return None


def create_resource(client, module):
    """Create a new tag definition."""
    tag_namespace_id = module.params["tag_namespace_id"]

    kwargs = dict(
        name=module.params["name"],
        description=module.params["description"],
    )

    if module.params.get("is_cost_tracking") is not None:
        kwargs["is_cost_tracking"] = module.params["is_cost_tracking"]

    validator = build_validator(module.params.get("validator"))
    if validator is not None:
        kwargs["validator"] = validator

    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags:
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags:
        kwargs["defined_tags"] = defined_tags

    details = CreateTagDetails(**kwargs)
    resource = call_with_retry(client.create_tag, tag_namespace_id, details).data

    if module.params.get("wait", True):
        resource = wait_for_resource(
            module,
            lambda rid: client.get_tag(tag_namespace_id, module.params["name"]),
            resource.id,
            target_states={LIFECYCLE_ACTIVE},
        )
    return resource


def update_resource(client, module, resource):
    """Update an existing tag definition."""
    tag_namespace_id = module.params.get("tag_namespace_id") or resource.tag_namespace_id

    kwargs = {}
    for attr in ("description", "is_cost_tracking", "is_retired"):
        value = module.params.get(attr)
        if value is not None and value != getattr(resource, attr, None):
            kwargs[attr] = value

    # Check validator changes
    desired_validator = module.params.get("validator")
    if desired_validator is not None:
        current_v = validator_to_dict(getattr(resource, "validator", None))
        desired_v = dict(desired_validator)
        if desired_v.get("values"):
            desired_v["values"] = sorted(desired_v["values"])
        if current_v != desired_v:
            kwargs["validator"] = build_validator(desired_validator)

    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        kwargs["freeform_tags"] = freeform_tags
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        kwargs["defined_tags"] = defined_tags

    if not kwargs:
        return resource

    details = UpdateTagDetails(**kwargs)
    resource = call_with_retry(client.update_tag, tag_namespace_id, resource.name, details).data
    return resource


def delete_resource(client, module, resource):
    """Delete a tag definition by retiring it and then deleting."""
    tag_namespace_id = module.params.get("tag_namespace_id") or resource.tag_namespace_id

    # Tags must be retired before deletion if not already
    if not getattr(resource, "is_retired", False):
        retire_details = UpdateTagDetails(is_retired=True)
        call_with_retry(client.update_tag, tag_namespace_id, resource.name, retire_details)

    call_with_retry(client.delete_tag, tag_namespace_id, resource.name)
    if module.params.get("wait", True):
        wait_for_resource(
            module,
            lambda rid: client.get_tag(tag_namespace_id, resource.name),
            resource.id,
            target_states={LIFECYCLE_DELETED, "TERMINATED"},
        )


def needs_update(module, resource):
    """Check if any attribute needs updating."""
    for attr in ("description", "is_cost_tracking", "is_retired"):
        desired = module.params.get(attr)
        if desired is not None and desired != getattr(resource, attr, None):
            return True

    desired_validator = module.params.get("validator")
    if desired_validator is not None:
        current_v = validator_to_dict(getattr(resource, "validator", None))
        desired_v = dict(desired_validator)
        if desired_v.get("values"):
            desired_v["values"] = sorted(desired_v["values"])
        if current_v != desired_v:
            return True

    freeform_tags = module.params.get("freeform_tags")
    defined_tags = module.params.get("defined_tags")
    if freeform_tags is not None and freeform_tags != getattr(resource, "freeform_tags", None):
        return True
    if defined_tags is not None and defined_tags != getattr(resource, "defined_tags", None):
        return True
    return False


def to_dict(resource):
    """Convert an OCI resource to a plain dict."""
    if resource is None:
        return {}
    result = {}
    for key, value in resource.__dict__.items():
        if key.startswith("_"):
            continue
        if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
            sub = {}
            for k, v in value.__dict__.items():
                if not k.startswith("_"):
                    sub[k] = v
            result[key] = sub
        else:
            result[key] = value
    return result


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "absent", ["tag_namespace_id"]),
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
