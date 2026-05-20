"""Unit tests for oracle.oci.oci_group module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_group"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_group(
    name='test-group',
    description='Test group',
):
    """Return a mock OCI group object."""
    group = MagicMock()
    group.name = 'test-group'
    group.description = 'Test group'
    group.id = "ocid1.test.oc1..testresource"
    group.compartment_id = "ocid1.tenancy.oc1..test"
    group.lifecycle_state = "ACTIVE"
    group.freeform_tags = {}
    group.defined_tags = {}
    return group


@pytest.fixture
def group_create_args(module_args):
    """Module args for creating a group."""
    module_args.update({
        "compartment_id": 'ocid1.tenancy.oc1..test',
        "name": 'test-group',
        "description": 'Test group',
        "group_id": None,
    })
    return module_args


class TestOciGroupCreate:
    """Test group creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_group(self, mock_create_client, group_create_args):
        """Creating a group calls create_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_group()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_group.return_value = mock_response

        module = MagicMock()
        module.params = group_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_group import create_resource
        result = create_resource(mock_client, module)

        mock_client.create_group.assert_called_once()


class TestOciGroupDelete:
    """Test group deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_group(self, mock_create_client, module_args):
        """Deleting a group calls delete_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "group_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_group import delete_resource
        delete_resource(mock_client, module, resource)

        mock_client.delete_group.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_group_already_gone(self, mock_create_client, module_args):
        """When group does not exist, get returns None via ServiceError 404."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_group.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "group_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_group import get_existing_resource
        result = get_existing_resource(mock_client, module)
        assert result is None


class TestOciGroupUpdate:
    """Test group update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_group(self, mock_create_client, module_args):
        """Updating a group calls update_group."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "group_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "description": "Updated description",
        })

        updated = _build_group(name="updated-group")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_group.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_group import update_resource
        result = update_resource(mock_client, module, resource)

        mock_client.update_group.assert_called_once()


class TestOciGroupIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test-group',
            "description": 'Test group',
            "compartment_id": None,
            "group_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_group()

        from ansible_collections.oracle.oci.plugins.modules.oci_group import needs_update
        assert not needs_update(module, resource)
