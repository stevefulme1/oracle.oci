# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Operations Insights Database Insight."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oci_opsi_database_insight
short_description: Manage a Database Insight resource in Oracle Cloud Infrastructure
description:
    - This module allows the user to create, update and delete a Database Insight resource in OCI
    - For I(state=present), creates a new Database Insight.
version_added: "2.0.0"
author: Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
            - Required for create using I(state=present).
        type: str
    entity_source:
        description:
            - Source of the database entity.
            - Required for create using I(state=present).
        type: str
        choices: ["MACS_MANAGED_EXTERNAL_DATABASE", "EM_MANAGED_EXTERNAL_DATABASE", "AUTONOMOUS_DATABASE"]
    database_id:
        description:
            - The OCID of the database.
        type: str
    database_resource_type:
        description:
            - Database resource type.
        type: str
    freeform_tags:
        description:
            - Simple key-value pair that is applied without any predefined name, type or scope.
            - This parameter is updatable.
        type: dict
    defined_tags:
        description:
            - Defined tags for this resource.
            - This parameter is updatable.
        type: dict
    database_insight_id:
        description:
            - The OCID of the Database Insight.
            - Required for update using I(state=present).
            - Required for delete using I(state=absent).
        type: str
        aliases: ["id"]
    state:
        description:
            - The state of the Database Insight.
            - Use I(state=present) to create or update a Database Insight.
            - Use I(state=absent) to delete a Database Insight.
        type: str
        required: false
        default: 'present'
        choices: ["present", "absent"]
extends_documentation_fragment: [
    stevefulme1.oci_cloud.oracle,
    stevefulme1.oci_cloud.oracle_creatable_resource,
    stevefulme1.oci_cloud.oracle_wait_options
]
"""

EXAMPLES = """
- name: Create database insight
  oci_opsi_database_insight:
    compartment_id: "{{ compartment_id }}"
    entity_source: "AUTONOMOUS_DATABASE"
    database_id: "{{ database_id }}"

- name: Update database insight
  oci_opsi_database_insight:
    database_insight_id: "{{ database_insight_id }}"
    freeform_tags:
      environment: production

- name: Delete database insight
  oci_opsi_database_insight:
    database_insight_id: "{{ database_insight_id }}"
    state: absent
"""

RETURN = """
database_insight:
    description:
        - Details of the Database Insight resource acted upon by the current operation
    returned: on success
    type: complex
    contains:
        id:
            description:
                - The OCID of the Database Insight.
            returned: on success
            type: str
            sample: "ocid1.databaseinsight.oc1..exampleuniqueID"
        compartment_id:
            description:
                - The OCID of the compartment.
            returned: on success
            type: str
            sample: "ocid1.compartment.oc1..exampleuniqueID"
        entity_source:
            description:
                - Source of the database entity.
            returned: on success
            type: str
            sample: AUTONOMOUS_DATABASE
        time_created:
            description:
                - The creation date and time of the Database Insight.
            returned: on success
            type: str
            sample: "2013-10-20T19:20:30+01:00"
        lifecycle_state:
            description:
                - The lifecycle state of the Database Insight.
            returned: on success
            type: str
            sample: ACTIVE
    sample: {
        "id": "ocid1.databaseinsight.oc1..exampleuniqueID",
        "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
        "entity_source": "AUTONOMOUS_DATABASE",
        "time_created": "2013-10-20T19:20:30+01:00",
        "lifecycle_state": "ACTIVE"
    }
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.opsi import OperationsInsightsClient
    from oci.opsi.models import CreateDatabaseInsightDetails, UpdateDatabaseInsightDetails

    HAS_OCI_PY_SDK = True
except ImportError:
    HAS_OCI_PY_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    DEAD_STATES,
    READY_STATES,
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
            choices=[
                "MACS_MANAGED_EXTERNAL_DATABASE",
                "EM_MANAGED_EXTERNAL_DATABASE",
                "AUTONOMOUS_DATABASE"
            ]
        ),
        database_id=dict(type="str"),
        database_resource_type=dict(type="str"),
        freeform_tags=dict(type="dict"),
        defined_tags=dict(type="dict"),
        database_insight_id=dict(type="str", aliases=["id"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )


def to_dict(resource):
    if resource is None:
        return {}
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            if isinstance(value, list):
                result[key] = [to_dict(i) if hasattr(i, "__dict__") else i for i in value]
            elif hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, dict)):
                result[key] = to_dict(value)
            else:
                result[key] = value
        return result
    return resource


def get_resource(client, module):
    try:
        return call_with_retry(client.get_database_insight, database_insight_id=module.params["database_insight_id"])
    except Exception as e:
        if "NotAuthorizedOrNotFound" in str(e) or "404" in str(e):
            return None
        raise


def find_resource(client, module):
    compartment_id = module.params.get("compartment_id")
    database_id = module.params.get("database_id")
    if not compartment_id:
        return None
    try:
        insights = call_with_retry(client.list_database_insights, compartment_id=compartment_id).data
        for insight in insights:
            if database_id and hasattr(insight, "database_id") and insight.database_id == database_id:
                if insight.lifecycle_state not in DEAD_STATES:
                    return call_with_retry(
                        client.get_database_insight,
                        database_insight_id=insight.id
                    )
    except Exception:
        pass
    return None


def create_resource(client, module):
    create_details = CreateDatabaseInsightDetails(
        compartment_id=module.params["compartment_id"],
        entity_source=module.params["entity_source"],
        database_id=module.params.get("database_id"),
        database_resource_type=module.params.get("database_resource_type"),
        freeform_tags=module.params.get("freeform_tags"),
        defined_tags=module.params.get("defined_tags"),
    )
    result = call_with_retry(client.create_database_insight, create_database_insight_details=create_details)
    resource = wait_for_resource(client.get_database_insight, result.data.id, READY_STATES, module)
    return resource


def update_resource(client, module):
    update_details = UpdateDatabaseInsightDetails(
        freeform_tags=module.params.get("freeform_tags"),
        defined_tags=module.params.get("defined_tags"),
    )
    call_with_retry(
        client.update_database_insight,
        database_insight_id=module.params["database_insight_id"],
        update_database_insight_details=update_details,
    )
    resource = wait_for_resource(
        client.get_database_insight,
        module.params["database_insight_id"],
        READY_STATES,
        module
    )
    return resource


def delete_resource(client, module):
    call_with_retry(
        client.delete_database_insight,
        database_insight_id=module.params["database_insight_id"]
    )
    wait_for_resource(
        client.get_database_insight,
        module.params["database_insight_id"],
        DEAD_STATES,
        module
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
    database_insight_id = module.params.get("database_insight_id")

    if database_insight_id:
        resource = get_resource(client, module)
    else:
        resource = find_resource(client, module)

    if state == "present":
        if resource:
            if needs_update(resource, module):
                if module.check_mode:
                    module.exit_json(
                        changed=True,
                        database_insight=to_dict(resource.data)
                    )
                resource = update_resource(client, module)
                module.exit_json(
                    changed=True,
                    database_insight=to_dict(resource.data)
                )
            else:
                module.exit_json(
                    changed=False,
                    database_insight=to_dict(resource.data)
                )
        else:
            if module.check_mode:
                module.exit_json(changed=True, database_insight={})
            resource = create_resource(client, module)
            module.exit_json(
                changed=True,
                database_insight=to_dict(resource.data)
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
