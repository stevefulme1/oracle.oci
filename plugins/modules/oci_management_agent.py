# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Management Agents."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_management_agent
short_description: Manage OCI Management Agents
description:
  - Read, update, and delete management agents in OCI.
  - Management agents are installed on hosts and cannot be created via the API.
  - This module supports updating agent properties and deleting agent registrations.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment.
      - Used for listing agents.
    type: str
  management_agent_id:
    description:
      - The OCID of the management agent.
      - Required for update and delete operations.
    type: str
  display_name:
    description:
      - A user-friendly name for the management agent.
    type: str
  freeform_tags:
    description:
      - Free-form tags for this resource.
    type: dict
  defined_tags:
    description:
      - Defined tags for this resource.
    type: dict
  state:
    description:
      - The desired state. Only present (update) and absent (delete) are supported.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Update a management agent display name
  oracle.oci.oci_management_agent:
    management_agent_id: "ocid1.managementagent.oc1..example"
    display_name: "prod-agent-01"
    state: present

- name: Delete a management agent
  oracle.oci.oci_management_agent:
    management_agent_id: "ocid1.managementagent.oc1..example"
    state: absent

- name: Read a management agent
  oracle.oci.oci_management_agent:
    management_agent_id: "ocid1.managementagent.oc1..example"
    state: present
"""

RETURN = r"""
resource:
  description: The management agent details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the management agent.
      type: str
    display_name:
      description: The display name of the agent.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    version:
      description: The agent version.
      type: str
    host:
      description: The host on which the agent is running.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    platform_type:
      description: The platform type (LINUX, WINDOWS).
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.management_agent import ManagementAgentClient
    from oci.management_agent.models import UpdateManagementAgentDetails
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


def get_agent(client, management_agent_id):
    """Get a management agent by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_management_agent, management_agent_id)
        agent = response.data
        if agent.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return agent
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_agent(client, compartment_id, display_name):
    """Find a management agent by compartment and display name."""
    if not compartment_id or not display_name:
        return None
    agents = call_with_retry(
        client.list_management_agents,
        compartment_id,
        display_name=display_name,
    ).data
    for a in agents:
        if a.display_name == display_name and a.lifecycle_state not in ("DELETED", "TERMINATED"):
            return get_agent(client, a.id)
    return None


def update_agent(module, client, agent):
    """Update an existing management agent."""
    kwargs = {}
    if module.params.get("display_name") is not None:
        kwargs["display_name"] = module.params["display_name"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return agent

    details = UpdateManagementAgentDetails(**kwargs)
    response = call_with_retry(client.update_management_agent, agent.id, details)
    return response.data


def delete_agent(module, client, agent):
    """Delete a management agent."""
    call_with_retry(client.delete_management_agent, agent.id)


def needs_update(module, agent):
    """Check if the agent needs updating."""
    if module.params.get("display_name") is not None:
        if agent.display_name != module.params["display_name"]:
            return True
    if module.params.get("freeform_tags") is not None:
        if getattr(agent, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(agent, "defined_tags", None) != module.params["defined_tags"]:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        management_agent_id=dict(type="str"),
        display_name=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, ManagementAgentClient)
    state = module.params.get("state", "present")
    management_agent_id = module.params.get("management_agent_id")

    # Get existing resource
    agent = None
    if management_agent_id:
        agent = get_agent(client, management_agent_id)
    elif module.params.get("compartment_id") and module.params.get("display_name"):
        agent = find_agent(client, module.params["compartment_id"], module.params["display_name"])

    if state == "absent":
        if agent is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_agent(module, client, agent)
        module.exit_json(changed=True)
        return

    # state == present: read/update only (agents cannot be created via API)
    if agent is None:
        module.fail_json(msg="Management agent not found. Agents must be installed on hosts, not created via API.")

    if needs_update(module, agent):
        if module.check_mode:
            module.exit_json(changed=True)
        agent = update_agent(module, client, agent)
        module.exit_json(changed=True, resource=to_dict(agent))
        return

    module.exit_json(changed=False, resource=to_dict(agent))


def main():
    run_module()


if __name__ == "__main__":
    main()
