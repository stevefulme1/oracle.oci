# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing OCI Notification Subscriptions."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_notification_subscription
short_description: Manage OCI Notification Subscriptions
description:
  - Create, update, and delete notification subscriptions in OCI.
  - Subscriptions deliver notifications from topics to endpoints via various protocols.
version_added: "1.0.0"
author: Oracle (@oracle)
options:
  compartment_id:
    description:
      - The OCID of the compartment.
      - Required when creating.
    type: str
  subscription_id:
    description:
      - The OCID of the subscription.
      - Required for update and delete operations.
    type: str
  topic_id:
    description:
      - The OCID of the topic for the subscription.
      - Required when creating.
    type: str
  protocol:
    description:
      - The protocol used for the subscription.
      - Required when creating.
    type: str
    choices: [EMAIL, HTTPS, SLACK, PAGERDUTY, ORACLE_FUNCTIONS]
  endpoint:
    description:
      - The endpoint that receives notifications.
      - "For EMAIL: an email address."
      - "For HTTPS: a URL."
      - "For SLACK: a Slack webhook URL."
      - "For PAGERDUTY: a PagerDuty integration key."
      - "For ORACLE_FUNCTIONS: a function OCID."
      - Required when creating.
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
      - The desired state of the subscription.
    type: str
    default: present
    choices: [present, absent]
extends_documentation_fragment:
  - oracle.oci.oci_common
"""

EXAMPLES = r"""
- name: Create an email notification subscription
  oracle.oci.oci_notification_subscription:
    compartment_id: "ocid1.compartment.oc1..example"
    topic_id: "ocid1.onstopic.oc1..example"
    protocol: EMAIL
    endpoint: "admin@example.com"
    state: present

- name: Create an HTTPS notification subscription
  oracle.oci.oci_notification_subscription:
    compartment_id: "ocid1.compartment.oc1..example"
    topic_id: "ocid1.onstopic.oc1..example"
    protocol: HTTPS
    endpoint: "https://hooks.example.com/webhook"
    state: present

- name: Create a Slack notification subscription
  oracle.oci.oci_notification_subscription:
    compartment_id: "ocid1.compartment.oc1..example"
    topic_id: "ocid1.onstopic.oc1..example"
    protocol: SLACK
    endpoint: "https://hooks.slack.com/services/T00/B00/XXXX"
    state: present

- name: Delete a subscription
  oracle.oci.oci_notification_subscription:
    subscription_id: "ocid1.onssubscription.oc1..example"
    state: absent
"""

RETURN = r"""
resource:
  description: The subscription details.
  returned: on success
  type: dict
  contains:
    id:
      description: The OCID of the subscription.
      type: str
    topic_id:
      description: The OCID of the topic.
      type: str
    compartment_id:
      description: The OCID of the compartment.
      type: str
    protocol:
      description: The protocol used.
      type: str
    endpoint:
      description: The endpoint receiving notifications.
      type: str
    lifecycle_state:
      description: The current lifecycle state.
      type: str
    created_time:
      description: The time the subscription was created.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry

try:
    import oci
    from oci.ons import NotificationDataPlaneClient
    from oci.ons.models import (
        CreateSubscriptionDetails,
        UpdateSubscriptionDetails,
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


def get_subscription(client, subscription_id):
    """Get a subscription by OCID, return None if not found."""
    try:
        response = call_with_retry(client.get_subscription, subscription_id)
        subscription = response.data
        if subscription.lifecycle_state in ("DELETED", "TERMINATED"):
            return None
        return subscription
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            return None
        raise


def find_subscription(client, compartment_id, topic_id, protocol, endpoint):
    """Find a subscription by compartment, topic, protocol, and endpoint."""
    if not compartment_id or not topic_id:
        return None
    subscriptions = call_with_retry(
        client.list_subscriptions,
        compartment_id,
    ).data
    for s in subscriptions:
        if (s.topic_id == topic_id
                and s.protocol == protocol
                and s.endpoint == endpoint
                and s.lifecycle_state not in ("DELETED", "TERMINATED")):
            return get_subscription(client, s.id)
    return None


def create_subscription(module, client):
    """Create a new notification subscription."""
    freeform_tags = module.params.get("freeform_tags") or {}
    defined_tags = module.params.get("defined_tags") or {}

    details = CreateSubscriptionDetails(
        compartment_id=module.params["compartment_id"],
        topic_id=module.params["topic_id"],
        protocol=module.params["protocol"],
        endpoint=module.params["endpoint"],
        freeform_tags=freeform_tags,
        defined_tags=defined_tags,
    )
    response = call_with_retry(client.create_subscription, details)
    return response.data


def update_subscription(module, client, subscription):
    """Update an existing subscription."""
    kwargs = {}
    if module.params.get("freeform_tags") is not None:
        kwargs["freeform_tags"] = module.params["freeform_tags"]
    if module.params.get("defined_tags") is not None:
        kwargs["defined_tags"] = module.params["defined_tags"]

    if not kwargs:
        return subscription

    details = UpdateSubscriptionDetails(**kwargs)
    response = call_with_retry(
        client.update_subscription,
        subscription.id,
        details,
    )
    return response.data


def delete_subscription(module, client, subscription):
    """Delete a notification subscription."""
    call_with_retry(client.delete_subscription, subscription.id)


def needs_update(module, subscription):
    """Check if the subscription needs updating."""
    if module.params.get("freeform_tags") is not None:
        if getattr(subscription, "freeform_tags", None) != module.params["freeform_tags"]:
            return True
    if module.params.get("defined_tags") is not None:
        if getattr(subscription, "defined_tags", None) != module.params["defined_tags"]:
            return True
    return False


def run_module():
    """Main module execution."""
    module_args = dict(
        compartment_id=dict(type="str"),
        subscription_id=dict(type="str"),
        topic_id=dict(type="str"),
        protocol=dict(
            type="str",
            choices=["EMAIL", "HTTPS", "SLACK", "PAGERDUTY", "ORACLE_FUNCTIONS"],
        ),
        endpoint=dict(type="str"),
        state=dict(type="str", default="present", choices=["present", "absent"]),
    )
    module_args.update(OCI_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ("state", "present", ("compartment_id", "topic_id", "protocol", "endpoint"), True),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    client = create_service_client(module, NotificationDataPlaneClient)
    state = module.params.get("state", "present")
    subscription_id = module.params.get("subscription_id")

    # Get existing resource
    subscription = None
    if subscription_id:
        subscription = get_subscription(client, subscription_id)
    elif (module.params.get("compartment_id") and module.params.get("topic_id")
            and module.params.get("protocol") and module.params.get("endpoint")):
        subscription = find_subscription(
            client,
            module.params["compartment_id"],
            module.params["topic_id"],
            module.params["protocol"],
            module.params["endpoint"],
        )

    if state == "absent":
        if subscription is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        delete_subscription(module, client, subscription)
        module.exit_json(changed=True)
        return

    # state == present
    if subscription is None:
        if not module.params.get("compartment_id") or not module.params.get("topic_id"):
            module.fail_json(
                msg="compartment_id, topic_id, protocol, and endpoint are required to create a subscription."
            )
        if module.check_mode:
            module.exit_json(changed=True)
        subscription = create_subscription(module, client)
        module.exit_json(changed=True, resource=to_dict(subscription))
        return

    if needs_update(module, subscription):
        if module.check_mode:
            module.exit_json(changed=True)
        subscription = update_subscription(module, client, subscription)
        module.exit_json(changed=True, resource=to_dict(subscription))
        return

    module.exit_json(changed=False, resource=to_dict(subscription))


def main():
    run_module()


if __name__ == "__main__":
    main()
