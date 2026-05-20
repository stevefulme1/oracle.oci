"""Unit tests for oracle.oci.oci_log_group module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_log_group"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_log_group(
    display_name="my-log-group",
    description="Test log group",
):
    """Return a mock OCI log group object."""
    log_group = MagicMock()
    log_group.display_name = display_name
    log_group.description = description
    log_group.id = "ocid1.loggroup.oc1..testresource"
    log_group.compartment_id = "ocid1.compartment.oc1..test"
    log_group.lifecycle_state = "ACTIVE"
    log_group.freeform_tags = {}
    log_group.defined_tags = {}
    return log_group


@pytest.fixture
def log_group_create_args(module_args):
    """Module args for creating a log group."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "display_name": "my-log-group",
        "description": "Test log group",
        "log_group_id": None,
    })
    return module_args


class TestOciLogGroupCreate:
    """Test log group creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_log_group(self, mock_create_client, log_group_create_args):
        """Creating a log group calls create_log_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_log_group()
        mock_response = MagicMock()
        mock_response.data = created
        mock_response.headers = {"location": "/logGroups/ocid1.loggroup.oc1..testresource"}
        mock_client.create_log_group.return_value = mock_response

        module = MagicMock()
        module.params = log_group_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_log_group import create_log_group
        result = create_log_group(module, mock_client)

        mock_client.create_log_group.assert_called_once()


class TestOciLogGroupDelete:
    """Test log group deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_log_group(self, mock_create_client, module_args):
        """Deleting a log group calls delete_log_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "absent",
            "log_group_id": "ocid1.loggroup.oc1..testresource",
            "compartment_id": None,
            "display_name": None,
            "description": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_log_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_log_group import delete_log_group
        delete_log_group(module, mock_client, resource)

        mock_client.delete_log_group.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_log_group_already_gone(self, mock_create_client, module_args):
        """When log group does not exist, get_log_group returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_log_group.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        from ansible_collections.oracle.oci.plugins.modules.oci_log_group import get_log_group
        result = get_log_group(mock_client, "ocid1.loggroup.oc1..nonexistent")
        assert result is None


class TestOciLogGroupUpdate:
    """Test log group update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_log_group(self, mock_create_client, module_args):
        """Updating a log group calls update_log_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "state": "present",
            "display_name": "updated-log-group",
            "log_group_id": "ocid1.loggroup.oc1..testresource",
            "compartment_id": None,
            "description": None,
        })

        updated = _build_log_group(display_name="updated-log-group")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_log_group.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_log_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_log_group import update_log_group
        result = update_log_group(module, mock_client, resource)

        mock_client.update_log_group.assert_called_once()


class TestOciLogGroupIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": "my-log-group",
            "description": "Test log group",
            "log_group_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_log_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_log_group import needs_update
        assert not needs_update(module, resource)
