# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Notification topics."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_notification_topic
short_description: Manage OCI Notification topics
description:
  - Create, update, and delete notification topics in OCI Notifications service.
  - Topics are communication channels for publishing messages to subscriptions.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment where the topic resides.
      - Required when creating a new topic.
    type: str
  name:
    description:
      - The name of the topic.
      - Must be unique within the compartment and cannot be changed after creation.
      - Required when creating a new topic.
    type: str
  description:
    description:
      - The description of the topic.
    type: str
  topic_id:
    description:
      - The OCID of the topic.
      - Required for update and delete operations.
    type: str
  state:
    description:
      - The desired state of the topic.
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
- name: Create a notification topic
  stevefulme1.oci_cloud.oci_notification_topic:
    compartment_id: ocid1.compartment.oc1..example
    name: my-alerts-topic
    description: Topic for critical alerts
    state: present

- name: Update a topic description
  stevefulme1.oci_cloud.oci_notification_topic:
    topic_id: ocid1.onstopic.oc1..example
    description: Updated topic description
    state: present

- name: Delete a notification topic
  stevefulme1.oci_cloud.oci_notification_topic:
    topic_id: ocid1.onstopic.oc1..example
    state: absent
"""

RETURN = r"""
resource:
  description: The notification topic resource details.
  returned: on success
  type: dict
  contains:
    topic_id:
      description: The OCID of the topic.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    name:
      description: The name of the topic.
      type: str
    description:
      description: The description of the topic.
      type: str
    lifecycle_state:
      description: The current lifecycle state of the topic.
      type: str
    time_created:
      description: The date and time the topic was created.
      type: str
    api_endpoint:
      description: The endpoint for managing subscriptions or publishing messages.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
    to_dict,
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
    from oci.ons import NotificationControlPlaneClient
    from oci.ons.models import (
        CreateTopicDetails,
        TopicAttributesDetails,
    )
    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False


def get_topic(client, topic_id):
    """Get a topic by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_topic, topic_id)
        topic = response.data
        if topic.lifecycle_state in ("DELETED",):
            return None
        return topic
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_topic(client, compartment_id, name):
    """Find a topic by compartment and name."""
    if not compartment_id or not name:
        return None
    topics = call_with_retry(
        client.list_topics,
        compartment_id,
    ).data
    for t in topics:
        if t.name == name and t.lifecycle_state not in ("DELETED",):
            return get_topic(client, t.topic_id)
    return None


def create_topic(module, client):
    """Create a new notification topic."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    kwargs = dict(
        compartment_id=module.params["compartment_id"],
        name=module.params["name"],
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    if module.params.get("description") is not None:
        kwargs["description"] = module.params["description"]

    details = CreateTopicDetails(**kwargs)
    response = call_with_retry(client.create_topic, details)
    topic = response.data

    if module.params.get("wait", True):
        topic = wait_for_resource(
            module,
            client.get_topic,
            topic.topic_id,
            target_states={"ACTIVE"},
        )
    return topic


def update_topic(module, client, topic):
    """Update an existing notification topic."""
    kwargs = {}
    if module.params.get("description") is not None:
        kwargs["description"] = module.params["description"]
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return topic

    details = TopicAttributesDetails(**kwargs)
    response = call_with_retry(client.update_topic, topic.topic_id, details)
    return response.data


def delete_topic(module, client, topic):
    """Delete a notification topic."""
    call_with_retry(client.delete_topic, topic.topic_id)

    if module.params.get("wait", True):
        wait_for_resource(
            module,
            client.get_topic,
            topic.topic_id,
            target_states={"DELETED"},
        )


def needs_update(module, topic):
    """Check if topic needs to be updated."""
    if (module.params.get("description") is not None
            and getattr(topic, "description", None) != module.params["description"]):
        return True
    freeform = module.params.get("freeform_tags")
    if freeform is not None and getattr(topic, "freeform_tags", None) != freeform:
        return True
    defined = module.params.get("defined_tags")
    if defined is not None and getattr(topic, "defined_tags", None) != defined:
        return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        name=dict(type="str"),
        description=dict(type="str"),
        topic_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "name"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, NotificationControlPlaneClient)
    state = module.params.get("state", "present")
    topic_id = module.params.get("topic_id")

    # Get existing resource
    topic = None
    if topic_id:
        topic = get_topic(client, topic_id)
    elif module.params.get("compartment_id") and module.params.get("name"):
        topic = find_topic(client, module.params["compartment_id"], module.params["name"])

    if state == "absent":
        if topic is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_topic(module, client, topic)
        module.exit_json(changed=True)
        return

    # state == present
    if topic is None:
        if not module.params.get("compartment_id") or not module.params.get("name"):
            module.fail_json(msg="compartment_id and name are required to create a topic.")
        if module.check_mode:
            module.exit_json(changed=True)
        topic = create_topic(module, client)
        module.exit_json(changed=True, resource=to_dict(topic))
        return

    if needs_update(module, topic):
        if module.check_mode:
            module.exit_json(changed=True)
        topic = update_topic(module, client, topic)
        module.exit_json(changed=True, resource=to_dict(topic))
        return

    module.exit_json(changed=False, resource=to_dict(topic))


def main():
    run_module()


if __name__ == "__main__":
    main()
