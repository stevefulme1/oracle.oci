"""Unit tests for oracle.oci.oci_alarm module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_alarm"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_alarm(
    display_name="high-cpu-alarm",
    namespace="oci_computeagent",
    query="CpuUtilization[1m].mean() > 80",
    severity="CRITICAL",
):
    """Return a mock OCI alarm object."""
    alarm = MagicMock()
    alarm.display_name = display_name
    alarm.namespace = namespace
    alarm.query = query
    alarm.severity = severity
    alarm.id = "ocid1.alarm.oc1..testresource"
    alarm.compartment_id = "ocid1.compartment.oc1..test"
    alarm.metric_compartment_id = "ocid1.compartment.oc1..test"
    alarm.destinations = ["ocid1.onstopic.oc1..test"]
    alarm.is_enabled = True
    alarm.lifecycle_state = "ACTIVE"
    alarm.freeform_tags = {}
    alarm.defined_tags = {}
    return alarm


@pytest.fixture
def alarm_create_args(module_args):
    """Module args for creating an alarm."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "display_name": "high-cpu-alarm",
        "metric_compartment_id": "ocid1.compartment.oc1..test",
        "namespace": "oci_computeagent",
        "query": "CpuUtilization[1m].mean() > 80",
        "severity": "CRITICAL",
        "destinations": ["ocid1.onstopic.oc1..test"],
        "is_enabled": True,
        "alarm_id": None,
    })
    return module_args


class TestOciAlarmCreate:
    """Test alarm creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_alarm(self, mock_create_client, alarm_create_args):
        """Creating an alarm calls create_alarm."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_alarm()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_alarm.return_value = mock_response

        module = MagicMock()
        module.params = alarm_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_alarm import create_alarm
        result = create_alarm(module, mock_client)

        mock_client.create_alarm.assert_called_once()


class TestOciAlarmDelete:
    """Test alarm deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_alarm(self, mock_create_client, module_args):
        """Deleting an alarm calls delete_alarm."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "alarm_id": "ocid1.alarm.oc1..testresource",
            "compartment_id": None,
            "display_name": None,
            "metric_compartment_id": None,
            "namespace": None,
            "query": None,
            "severity": None,
            "destinations": None,
            "is_enabled": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_alarm()

        from ansible_collections.oracle.oci.plugins.modules.oci_alarm import delete_alarm
        delete_alarm(module, mock_client, resource)

        mock_client.delete_alarm.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_alarm_already_gone(self, mock_create_client, module_args):
        """When alarm does not exist, get_alarm returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_alarm.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_alarm import get_alarm
        result = get_alarm(mock_client, "ocid1.alarm.oc1..nonexistent")
        assert result is None


class TestOciAlarmUpdate:
    """Test alarm update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_alarm(self, mock_create_client, module_args):
        """Updating an alarm calls update_alarm."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "display_name": "updated-alarm",
            "alarm_id": "ocid1.alarm.oc1..testresource",
            "compartment_id": None,
            "metric_compartment_id": None,
            "namespace": None,
            "query": None,
            "severity": None,
            "destinations": None,
            "is_enabled": None,
        })

        updated = _build_alarm(display_name="updated-alarm")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_alarm.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_alarm()

        from ansible_collections.oracle.oci.plugins.modules.oci_alarm import update_alarm
        result = update_alarm(module, mock_client, resource)

        mock_client.update_alarm.assert_called_once()


class TestOciAlarmIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "high-cpu-alarm",
            "namespace": "oci_computeagent",
            "query": "CpuUtilization[1m].mean() > 80",
            "severity": "CRITICAL",
            "destinations": None,
            "is_enabled": None,
            "metric_compartment_id": None,
            "alarm_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_alarm()

        from ansible_collections.oracle.oci.plugins.modules.oci_alarm import needs_update
        assert not needs_update(module, resource)
