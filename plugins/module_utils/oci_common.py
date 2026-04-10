"""Common OCI argument specs and constants used across all modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


OCI_COMMON_ARGS = dict(
    config_file_location=dict(type="str", default="~/.oci/config"),
    config_profile_name=dict(type="str", default="DEFAULT"),
    auth_type=dict(
        type="str",
        default="api_key",
        choices=["api_key", "instance_principal", "resource_principal", "session_token"],
    ),
    tenancy=dict(type="str"),
    region=dict(type="str"),
    api_user=dict(type="str"),
    api_user_fingerprint=dict(type="str", no_log=True),
    api_user_key_file=dict(type="str"),
    api_user_key_pass_phrase=dict(type="str", no_log=True),
    wait=dict(type="bool", default=True),
    wait_timeout=dict(type="int", default=1200),
    wait_interval=dict(type="int", default=30),
    freeform_tags=dict(type="dict"),
    defined_tags=dict(type="dict"),
)

LIFECYCLE_ACTIVE = "ACTIVE"
LIFECYCLE_AVAILABLE = "AVAILABLE"
LIFECYCLE_RUNNING = "RUNNING"
LIFECYCLE_PROVISIONING = "PROVISIONING"
LIFECYCLE_CREATING = "CREATING"
LIFECYCLE_DELETED = "DELETED"
LIFECYCLE_DELETING = "DELETING"
LIFECYCLE_TERMINATED = "TERMINATED"
LIFECYCLE_TERMINATING = "TERMINATING"
LIFECYCLE_FAILED = "FAILED"
LIFECYCLE_STOPPED = "STOPPED"

WAIT_STATES = frozenset({
    LIFECYCLE_PROVISIONING,
    LIFECYCLE_CREATING,
    LIFECYCLE_DELETING,
    LIFECYCLE_TERMINATING,
})

READY_STATES = frozenset({
    LIFECYCLE_ACTIVE,
    LIFECYCLE_AVAILABLE,
    LIFECYCLE_RUNNING,
})

DEAD_STATES = frozenset({
    LIFECYCLE_DELETED,
    LIFECYCLE_TERMINATED,
})
