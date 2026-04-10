#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Events rules."""

from __future__ import annotations

DOCUMENTATION = r"""
---
module: oci_events_rule
short_description: Manage OCI Events rules
description:
  - Create, update, and delete event rules in OCI Events service.
  - Event rules match events emitted by OCI services and route them to actions
    such as notifications, streaming, or function invocations.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the rule resides.
      - Required when creating a new rule.
    type: str
  display_name:
    description:
      - A user-friendly name for the event rule.
      - Required when creating a new rule.
    type: str
  description:
    description:
      - A description of the event rule.
    type: str
  condition:
    description:
      - A JSON string specifying the filter condition for events.
      - 'Example: {"eventType": ["com.oraclecloud.objectstorage.createbucket"]}'
      - Required when creating a new rule.
    type: str
  is_enabled:
    description:
      - Whether the rule is enabled.
    type: bool
    default: true
  actions:
    description:
      - List of actions to execute when an event matches the rule.
      - Each action is a dict with C(action_type) and the target resource ID.
    type: list
    elements: dict
    suboptions:
      action_type:
        description:
          - The type of action to perform.
        type: str
        choices: [ONS, OSS, FAAS]
        required: true
      topic_id:
        description:
          - The OCID of the notification topic (for ONS action_type).
        type: str
      stream_id:
        description:
          - The OCID of the stream (for OSS action_type).
        type: str
      function_id:
        description:
          - The OCID of the function (for FAAS action_type).
        type: str
      is_enabled:
        description:
          - Whether this action is enabled.
        type: bool
        default: true
  rule_id:
    description:
      - The OCID of the event rule.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the event rule.
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
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an event rule for bucket creation
  oracle.oci.oci_events_rule:
    compartment_id: ocid1.compartment.oc1..example
    display_name: bucket-creation-alert
    description: Alert when a new bucket is created
    condition: '{"eventType": ["com.oraclecloud.objectstorage.createbucket"]}'
    is_enabled: true
    actions:
      - action_type: ONS
        topic_id: ocid1.onstopic.oc1..example
        is_enabled: true
    state: present

- name: Create a rule with streaming action
  oracle.oci.oci_events_rule:
    compartment_id: ocid1.compartment.oc1..example
    display_name: audit-to-stream
    condition: '{"eventType": ["com.oraclecloud.identitycontrolplane.createuser"]}'
    actions:
      - action_type: OSS
        stream_id: ocid1.stream.oc1..example
    state: present

- name: Create a rule with function invocation
  oracle.oci.oci_events_rule:
    compartment_id: ocid1.compartment.oc1..example
    display_name: auto-remediate
    condition: '{"eventType": ["com.oraclecloud.cloudguard.problemdetected"]}'
    actions:
      - action_type: FAAS
        function_id: ocid1.fnfunc.oc1..example
    state: present

- name: Disable an event rule
  oracle.oci.oci_events_rule:
    rule_id: ocid1.eventrule.oc1..example
    is_enabled: false
    state: present

- name: Delete an event rule
  oracle.oci.oci_events_rule:
    rule_id: ocid1.eventrule.oc1..example
    state: absent
"""

RETURN = r"""
resource:
  description: The event rule resource details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the event rule.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    display_name:
      description: The display name of the rule.
      type: str
    description:
      description: The description of the rule.
      type: str
    condition:
      description: The JSON filter condition.
      type: str
    is_enabled:
      description: Whether the rule is enabled.
      type: bool
    actions:
      description: The list of actions configured for the rule.
      type: dict
    lifecycle_state:
      description: The current lifecycle state of the rule.
      type: str
    time_created:
      description: The date and time the rule was created.
      type: str
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import (
    create_service_client,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)

try:
    import oci
    from oci.events import EventsClient
    from oci.events.models import (
        CreateRuleDetails,
        UpdateRuleDetails,
        ActionDetailsList,
        ActionDetails,
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


def get_rule(client, rule_id):
    """Get an event rule by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_rule, rule_id)
        rule = response.data
        if rule.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return rule
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_rule(client, compartment_id, display_name):
    """Find a rule by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    rules = call_with_retry(
        client.list_rules,
        compartment_id,
    ).data
    for r in rules:
        if r.display_name == display_name and r.lifecycle_state not in (
            "DELETED",
            "TERMINATED",
        ):
            return get_rule(client, r.id)
    return None


def build_actions(action_list):
    """Build ActionDetailsList from the module params actions list."""
    if not action_list:
        return None

    actions = []
    for item in action_list:
        action_type = item["action_type"]
        is_enabled = item.get("is_enabled", True)

        if action_type == "ONS":
            actions.append(
                ActionDetails(
                    action_type="ONS",
                    topic_id=item.get("topic_id"),
                    is_enabled=is_enabled,
                )
            )
        elif action_type == "OSS":
            actions.append(
                ActionDetails(
                    action_type="OSS",
                    stream_id=item.get("stream_id"),
                    is_enabled=is_enabled,
                )
            )
        elif action_type == "FAAS":
            actions.append(
                ActionDetails(
                    action_type="FAAS",
                    function_id=item.get("function_id"),
                    is_enabled=is_enabled,
                )
            )
    return ActionDetailsList(actions=actions)


def create_rule(module, client):
    """Create a new event rule."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    actions = build_actions(module.params.get("actions"))

    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        display_name=module.params["display_name"],
        condition=module.params["condition"],
        is_enabled=module.params.get("is_enabled", True),
        actions=actions,
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    if module.params.get("description") is not None:
        kwargs["description"] = module.params["description"]

    details = CreateRuleDetails(**kwargs)
    response = call_with_retry(client.create_rule, details)
    rule = response.data

    if module.params.get("wait", True):
        rule = wait_for_resource(
            module,
            client.get_rule,
            rule.id,
            target_states={"ACTIVE"},
        )
    return rule


def update_rule(module, client, rule):
    """Update an existing event rule."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("description") is not None:
        kwargs["description"] = module.params["description"]
    if module.params.get("condition") is not None:
        kwargs["condition"] = module.params["condition"]
    if module.params.get("is_enabled") is not None:
        kwargs["is_enabled"] = module.params["is_enabled"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    actions = build_actions(module.params.get("actions"))
    if actions is not None:
        kwargs["actions"] = actions

    if not kwargs:
        return rule

    details = UpdateRuleDetails(**kwargs)
    response = call_with_retry(client.update_rule, rule.id, details)
    return response.data


def delete_rule(module, client, rule):
    """Delete an event rule."""
    call_with_retry(client.delete_rule, rule.id)

    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_rule,
            rule.id,
            target_states={"DELETED", "TERMINATED"},
        )


def needs_update(module, rule):
    """Check if rule needs to be updated."""
    check_attrs = ["display_name", "description", "condition", "is_enabled"]
    for attr in check_attrs:
        desired = module.params.get(attr)
        if desired is not None and getattr(rule, attr, None) != desired:
            return True
    # Actions comparison is complex; if actions param is provided, assume update needed
    if module.params.get("actions") is not None:
        return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(rule, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(rule, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        condition=dict(type="str"),
        is_enabled=dict(type="bool", default=True),
        actions=dict(
            type="list",
            elements="dict",
            options=dict(
                action_type=dict(type="str", choices=["ONS", "OSS", "FAAS"], required=True),
                topic_id=dict(type="str"),
                stream_id=dict(type="str"),
                function_id=dict(type="str"),
                is_enabled=dict(type="bool", default=True),
            ),
        ),
        rule_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "display_name", "condition", "actions"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, EventsClient)
    state = module.params.get("state", "present")
    rule_id = module.params.get("rule_id")

    # Get existing resource
    rule = None
    if rule_id:
        rule = get_rule(client, rule_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        rule = find_rule(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if rule is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_rule(module, client, rule)
        module.exit_json(changed=True)
        return

    # state == present
    if rule is None:
        if not module.params.get("compartment_id") or not module.params.get("display_name"):
            module.fail_json(msg="compartment_id, display_name, condition, and actions are required to create a rule.")
        if module.check_mode:
            module.exit_json(changed=True)
        rule = create_rule(module, client)
        module.exit_json(changed=True, resource=to_dict(rule))
        return

    if needs_update(module, rule):
        if module.check_mode:
            module.exit_json(changed=True)
        rule = update_rule(module, client, rule)
        module.exit_json(changed=True, resource=to_dict(rule))
        return

    module.exit_json(changed=False, resource=to_dict(rule))


def main():
    run_module()


if __name__ == "__main__":
    main()
