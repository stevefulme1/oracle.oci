# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Dashboard."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: oci_dashboard
short_description: Manage a Dashboard resource in Oracle Cloud Infrastructure
description:
    - This module allows the user to create, update and delete a Dashboard resource in Oracle Cloud Infrastructure
    - For I(state=present), creates a new Dashboard.
version_added: "2.1.0"
author: Oracle (@oracle)
options:
    dashboard_group_id:
        description:
            - The OCID of the Dashboard Group.
            - Required for create using I(state=present).
        type: str
    display_name:
        description:
            - The display name of the Dashboard.
            - This parameter is updatable.
        type: str
    description:
        description:
            - The description of the Dashboard.
            - This parameter is updatable.
        type: str
    schema_version:
        description:
            - The schema version of the dashboard.
        type: str
    config:
        description:
            - The dashboard configuration as a dict.
        type: dict
    widgets:
        description:
            - The list of widgets in the dashboard.
        type: list
        elements: dict
    dashboard_id:
        description:
            - The OCID of the Dashboard.
            - Required for update using I(state=present).
            - Required for delete using I(state=absent).
        type: str
        aliases: ["id"]
    state:
        description:
            - The state of the Dashboard.
            - Use I(state=present) to create or update a Dashboard.
            - Use I(state=absent) to delete a Dashboard.
        type: str
        required: false
        default: 'present'
        choices: ["present", "absent"]
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
"""

EXAMPLES = """
- name: Create dashboard
  oci_dashboard:
    dashboard_group_id: "{{ dashboard_group_id }}"
    display_name: "My Dashboard"
    description: "Dashboard for monitoring"
    schema_version: "v1"

- name: Update dashboard
  oci_dashboard:
    dashboard_id: "{{ dashboard_id }}"
    display_name: "Updated Dashboard"
    description: "Updated description"

- name: Delete dashboard
  oci_dashboard:
    dashboard_id: "{{ dashboard_id }}"
    state: absent
"""

RETURN = """
dashboard:
    description:
        - Details of the Dashboard resource acted upon by the current operation
    returned: on success
    type: complex
    contains:
        id:
            description:
                - The OCID of the Dashboard.
            returned: on success
            type: str
            sample: "ocid1.dashboard.oc1..exampleuniqueID"
        dashboard_group_id:
            description:
                - The OCID of the Dashboard Group.
            returned: on success
            type: str
            sample: "ocid1.dashboardgroup.oc1..exampleuniqueID"
        display_name:
            description:
                - The display name of the Dashboard.
            returned: on success
            type: str
            sample: My Dashboard
        description:
            description:
                - The description of the Dashboard.
            returned: on success
            type: str
            sample: Dashboard for monitoring
        time_created:
            description:
                - The creation date and time of the Dashboard.
            returned: on success
            type: str
            sample: "2013-10-20T19:20:30+01:00"
        lifecycle_state:
            description:
                - The lifecycle state of the Dashboard.
            returned: on success
            type: str
            sample: ACTIVE
    sample: {
        "id": "ocid1.dashboard.oc1..exampleuniqueID",
        "dashboard_group_id": "ocid1.dashboardgroup.oc1..exampleuniqueID",
        "display_name": "My Dashboard",
        "description": "Dashboard for monitoring",
        "time_created": "2013-10-20T19:20:30+01:00",
        "lifecycle_state": "ACTIVE"
    }
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.exceptions import ServiceError
    from oci.dashboard_service import DashboardClient
    from oci.dashboard_service.models import CreateDashboardDetails, UpdateDashboardDetails

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
        dashboard_group_id=dict(type="str"),
        display_name=dict(type="str"),
        description=dict(type="str"),
        schema_version=dict(type="str"),
        config=dict(type="dict"),
        widgets=dict(type="list", elements="dict"),
        dashboard_id=dict(type="str", aliases=["id"]),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )


def get_resource(client, module):
    try:
        return call_with_retry(client.get_dashboard, dashboard_id=module.params["dashboard_id"])
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, module):
    dashboard_group_id = module.params.get("dashboard_group_id")
    display_name = module.params.get("display_name")
    if not dashboard_group_id or not display_name:
        return None
    try:
        dashboards = call_with_retry(client.list_dashboards, dashboard_group_id=dashboard_group_id).data
        for dashboard in dashboards:
            if dashboard.display_name == display_name and dashboard.lifecycle_state not in DEAD_STATES:
                return call_with_retry(client.get_dashboard, dashboard_id=dashboard.id)
    except ServiceError:
        pass
    return None


def create_resource(client, module):
    create_details = CreateDashboardDetails(
        dashboard_group_id=module.params["dashboard_group_id"],
        display_name=module.params.get("display_name"),
        description=module.params.get("description"),
        schema_version=module.params.get("schema_version"),
        config=module.params.get("config"),
        widgets=module.params.get("widgets"),
    )
    result = call_with_retry(client.create_dashboard, create_dashboard_details=create_details)
    resource = wait_for_resource(module, client.get_dashboard, result.data.id, READY_STATES)
    return resource


def update_resource(client, module):
    update_details = UpdateDashboardDetails(
        display_name=module.params.get("display_name"),
        description=module.params.get("description"),
    )
    call_with_retry(
        client.update_dashboard,
        dashboard_id=module.params["dashboard_id"],
        update_dashboard_details=update_details
    )
    resource = wait_for_resource(
        module, client.get_dashboard, module.params["dashboard_id"], READY_STATES
    )
    return resource


def delete_resource(client, module):
    call_with_retry(
        client.delete_dashboard,
        dashboard_id=module.params["dashboard_id"]
    )
    wait_for_resource(
        module, client.get_dashboard, module.params["dashboard_id"], DEAD_STATES
    )


def needs_update(resource, module):
    desired_name = module.params.get("display_name")
    if desired_name and resource.data.display_name != desired_name:
        return True
    desired_desc = module.params.get("description")
    if desired_desc is not None and resource.data.description != desired_desc:
        return True
    return False


def main():
    module = AnsibleModule(argument_spec=dict(**get_module_args(), **OCI_COMMON_ARGS), supports_check_mode=True)

    if not HAS_OCI_PY_SDK:
        module.fail_json(msg="oci python sdk is required for this module")

    client = create_service_client(module, DashboardClient)

    state = module.params["state"]
    dashboard_id = module.params.get("dashboard_id")

    if dashboard_id:
        resource = get_resource(client, module)
    else:
        resource = find_resource(client, module)

    if state == "present":
        if resource:
            if needs_update(resource, module):
                if module.check_mode:
                    module.exit_json(
                        changed=True,
                        dashboard=to_dict(resource.data)
                    )
                resource = update_resource(client, module)
                module.exit_json(
                    changed=True,
                    dashboard=to_dict(resource.data)
                )
            else:
                module.exit_json(
                    changed=False,
                    dashboard=to_dict(resource.data)
                )
        else:
            if module.check_mode:
                module.exit_json(changed=True, dashboard={})
            resource = create_resource(client, module)
            module.exit_json(
                changed=True,
                dashboard=to_dict(resource.data)
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
