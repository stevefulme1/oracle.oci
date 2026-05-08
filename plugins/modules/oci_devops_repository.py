# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI DevOps Repositories."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_devops_repository
short_description: Manage DevOps Repositories in OCI
description:
    - Create, update, and delete DevOps Repositories in Oracle Cloud Infrastructure.
    - This module uses the OCI Python SDK C(oci.devops.DevopsClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    project_id:
        description:
            - The OCID of the DevOps project for the repository.
            - Required when creating a new repository.
        type: str
    repository_id:
        description:
            - The OCID of an existing repository.
            - Required for update and delete operations.
        type: str
    name:
        description:
            - The name of the repository.
            - Required when creating a new repository.
        type: str
    repository_type:
        description:
            - The type of repository.
        type: str
        choices:
            - HOSTED
            - MIRRORED
        default: HOSTED
    default_branch:
        description:
            - The default branch of the repository.
        type: str
    description:
        description:
            - A description of the repository.
        type: str
    state:
        description:
            - The desired state of the repository.
        type: str
        choices:
            - present
            - absent
        default: present
    wait:
        description:
            - Whether to wait for the resource to reach the desired state.
        type: bool
        default: true
    wait_timeout:
        description:
            - Maximum time in seconds to wait for the resource to reach the desired state.
        type: int
        default: 1200
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Create a DevOps repository
  stevefulme1.oci_cloud.oci_devops_repository:
    project_id: "ocid1.devopsproject.oc1..example"
    name: "my-repo"
    repository_type: HOSTED
    default_branch: "main"
    state: present

- name: Delete a DevOps repository
  stevefulme1.oci_cloud.oci_devops_repository:
    repository_id: "ocid1.devopsrepository.oc1..example"
    state: absent
"""

RETURN = r"""
devops_repository:
    description: Details of the DevOps repository.
    returned: On success when state is present.
    type: dict
    sample:
        id: "ocid1.devopsrepository.oc1..example"
        name: "my-repo"
        lifecycle_state: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.devops import DevopsClient
    from oci.devops.models import (
        CreateRepositoryDetails,
        UpdateRepositoryDetails,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

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
    module_args = dict(
        project_id=dict(type="str"),
        repository_id=dict(type="str"),
        name=dict(type="str"),
        repository_type=dict(type="str", choices=["HOSTED", "MIRRORED"], default="HOSTED"),
        default_branch=dict(type="str"),
        description=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def get_resource(client, resource_id):
    try:
        response = call_with_retry(client.get_repository, resource_id)
        return response.data
    except ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_resource(client, project_id, name):
    if not project_id:
        return None
    try:
        response = call_with_retry(client.list_repositories, project_id=project_id)
        for item in response.data.items:
            if item.lifecycle_state in DEAD_STATES:
                continue
            if name and item.name == name:
                return item
    except ServiceError:
        pass
    return None


def create_resource(module, client):
    params = module.params
    create_details = CreateRepositoryDetails(
        project_id=params["project_id"],
        name=params["name"],
        repository_type=params.get("repository_type"),
        default_branch=params.get("default_branch"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.create_repository, create_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_repository, resource.id, target_states=READY_STATES,
    )
    return resource


def update_resource(module, client, existing):
    params = module.params
    update_details = UpdateRepositoryDetails(
        name=params.get("name"),
        default_branch=params.get("default_branch"),
        description=params.get("description"),
        freeform_tags=params.get("freeform_tags"),
        defined_tags=params.get("defined_tags"),
    )
    response = call_with_retry(client.update_repository, existing.id, update_details)
    resource = response.data
    resource = wait_for_resource(
        module, client.get_repository, resource.id, target_states=READY_STATES,
    )
    return resource


def delete_resource(module, client, existing):
    call_with_retry(client.delete_repository, existing.id)
    wait_for_resource(
        module, client.get_repository, existing.id, target_states=DEAD_STATES,
    )


def needs_update(params, existing):
    updatable = ["name", "default_branch", "description"]
    for attr in updatable:
        desired = params.get(attr)
        if desired is None:
            continue
        current = getattr(existing, attr, None)
        if current != desired:
            return True
    if params.get("freeform_tags") is not None:
        if getattr(existing, "freeform_tags", None) != params["freeform_tags"]:
            return True
    if params.get("defined_tags") is not None:
        if getattr(existing, "defined_tags", None) != params["defined_tags"]:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("project_id", "name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, DevopsClient)
    params = module.params
    state = params["state"]

    existing = None
    if params.get("repository_id"):
        existing = get_resource(client, params["repository_id"])
    elif params.get("project_id"):
        existing = find_resource(client, params["project_id"], params.get("name"))

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_resource(module, client, existing)
        module.exit_json(changed=True)
        return

    if existing is None:
        for req in ("project_id", "name"):
            if not params.get(req):
                module.fail_json(msg=f"Parameter '{req}' is required to create a DevOps repository.")
        if module.check_mode:
            module.exit_json(changed=True)
        resource = create_resource(module, client)
        module.exit_json(changed=True, devops_repository=to_dict(resource))
        return

    if needs_update(params, existing):
        if module.check_mode:
            module.exit_json(changed=True)
        resource = update_resource(module, client, existing)
        module.exit_json(changed=True, devops_repository=to_dict(resource))
        return

    module.exit_json(changed=False, devops_repository=to_dict(existing))


if __name__ == "__main__":
    main()
