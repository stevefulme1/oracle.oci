# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Operations Insights Host Insight."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oci_opsi_host_insight
short_description: Manage a Host Insight resource in Oracle Cloud Infrastructure
description:
    - This module allows the user to create, update and delete a Host Insight resource in Oracle Cloud Infrastructure
    - For I(state=present), creates a new Host Insight.
version_added: "2.1.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required for create using I(state=present).
        type: str
    entity_source:
        description:
            - Source of the host entity.
            - Required for create using I(state=present).
        type: str
        choices: ["MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST"]
    management_agent_id:
        description:
            - The OCID of the Management Agent.
        type: str
    host_insight_id:
        description:
            - The OCID of the Host Insight.
            - Required for update using I(state=present).
            - Required for delete using I(state=absent).
        type: str
        aliases: ["id"]
    state:
        description:
            - The state of the Host Insight.
            - Use I(state=present) to create or update a Host Insight.
            - Use I(state=absent) to delete a Host Insight.
        type: str
        required: false
        default: 'present'
        choices: ["present", "absent"]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = """
- name: Create host insight
  oci_opsi_host_insight:
    compartment_id: "{{ compartment_id }}"
    entity_source: "MACS_MANAGED_EXTERNAL_HOST"
    management_agent_id: "{{ management_agent_id }}"

- name: Update host insight
  oci_opsi_host_insight:
    host_insight_id: "{{ host_insight_id }}"
    freeform_tags:
      environment: production

- name: Delete host insight
  oci_opsi_host_insight:
    host_insight_id: "{{ host_insight_id }}"
    state: absent
"""

RETURN = """
host_insight:
    description:
        - Details of the Host Insight resource acted upon by the current operation
    returned: on success
    type: complex
    contains:
        id:
            description:
                - The OCID of the Host Insight.
            returned: on success
            type: str
            sample: "ocid1.hostinsight.oc1..exampleuniqueID"
        compartment_id:
            description:
                - The OCID of the compartment.
            returned: on success
            type: str
            sample: "ocid1.compartment.oc1..exampleuniqueID"
        entity_source:
            description:
                - Source of the host entity.
            returned: on success
            type: str
            sample: MACS_MANAGED_EXTERNAL_HOST
        time_created:
            description:
                - The creation date and time of the Host Insight.
            returned: on success
            type: str
            sample: "2013-10-20T19:20:30+01:00"
        lifecycle_state:
            description:
                - The lifecycle state of the Host Insight.
            returned: on success
            type: str
            sample: ACTIVE
    sample: {
        "id": "ocid1.hostinsight.oc1..exampleuniqueID",
        "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
        "entity_source": "MACS_MANAGED_EXTERNAL_HOST",
        "time_created": "2013-10-20T19:20:30+01:00",
        "lifecycle_state": "ACTIVE"
    }
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.exceptions import ServiceError
    from oci.opsi import OperationsInsightsClient
    from oci.opsi.models import CreateHostInsightDetails, UpdateHostInsightDetails

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
    to_dict,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import (
    call_with_retry,
    wait_for_resource,
)


def get_module_args():
    return dict(
        compartment_id=dict(type="str"),
        entity_source=dict(
            type="str",
            choices=["MACS_MANAGED_EXTERNAL_HOST", "EM_MANAGED_EXTERNAL_HOST"]
        ),
        management_agent_id=dict(type="str"),
        host_insight_id=dict(type="str", aliases=["id"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )


def get_resource(client, module):
    try:
        return call_with_retry(client.get_host_insight, host_insight_id=module.params["host_insight_id"])
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, module):
    compartment_id = module.params.get("compartment_id")
    management_agent_id = module.params.get("management_agent_id")
    if not compartment_id:
        return None
    try:
        insights = call_with_retry(client.list_host_insights, compartment_id=compartment_id).data
        for insight in insights:
            has_agent = hasattr(insight, "management_agent_id")
            if management_agent_id and has_agent and insight.management_agent_id == management_agent_id:
                if insight.lifecycle_state not in DEAD_STATES:
                    return call_with_retry(
                        client.get_host_insight,
                        host_insight_id=insight.id
                    )
    except ServiceError:
        pass
    return None


def create_resource(client, module):
    create_details = CreateHostInsightDetails(
        compartment_id=module.params["compartment_id"],
        entity_source=module.params["entity_source"],
        management_agent_id=module.params.get("management_agent_id"),
        freeform_tags=module.params.get("freeform_tags"),
        defined_tags=module.params.get("defined_tags"),
    )
    result = call_with_retry(client.create_host_insight, create_host_insight_details=create_details)
    resource = wait_for_resource(module, client.get_host_insight, result.data.id, READY_STATES)
    return resource


def update_resource(client, module):
    update_details = UpdateHostInsightDetails(
        freeform_tags=module.params.get("freeform_tags"),
        defined_tags=module.params.get("defined_tags"),
    )
    call_with_retry(
        client.update_host_insight,
        host_insight_id=module.params["host_insight_id"],
        update_host_insight_details=update_details
    )
    resource = wait_for_resource(
        module, client.get_host_insight, module.params["host_insight_id"], READY_STATES
    )
    return resource


def delete_resource(client, module):
    call_with_retry(
        client.delete_host_insight,
        host_insight_id=module.params["host_insight_id"]
    )
    wait_for_resource(
        module, client.get_host_insight, module.params["host_insight_id"], DEAD_STATES
    )


def needs_update(resource, module):
    if module.params.get("freeform_tags") is not None:
        if resource.data.freeform_tags != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if resource.data.defined_tags != module.params["defined_tags"]:
            return True
    return False


def main():
    module = AnsibleModule(argument_spec=dict(**get_module_args(), **OCI_COMMON_ARGS), supports_check_mode=True)

    if not HAS_OCI_PY_SDK:
        module.fail_json(msg="oci python sdk is required for this module")

    client = create_service_client(module, OperationsInsightsClient)

    state = module.params["state"]
    host_insight_id = module.params.get("host_insight_id")

    if host_insight_id:
        resource = get_resource(client, module)
    else:
        resource = find_resource(client, module)

    if state == "present":
        if resource:
            if needs_update(resource, module):
                if module.check_mode:
                    module.exit_json(
                        changed=True,
                        host_insight=to_dict(resource.data)
                    )
                resource = update_resource(client, module)
                module.exit_json(
                    changed=True,
                    host_insight=to_dict(resource.data)
                )
            else:
                module.exit_json(
                    changed=False,
                    host_insight=to_dict(resource.data)
                )
        else:
            if module.check_mode:
                module.exit_json(changed=True, host_insight={})
            resource = create_resource(client, module)
            module.exit_json(
                changed=True,
                host_insight=to_dict(resource.data)
            )
    elif state == "absent":
        if resource:
            if module.check_mode:
                module.exit_json(changed=True)
            delete_resource(client, module)
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


if __name__ == "__main__":
    main()
