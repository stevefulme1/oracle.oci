"""Unit tests for oracle.oci.oci_user module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_user"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_user(
    name='test-user',
    description='Test user',
    email='test@example.com',
):
    """Return a mock OCI user object."""
    user = MagicMock()
    user.name = 'test-user'
    user.description = 'Test user'
    user.email = 'test@example.com'
    user.id = "ocid1.test.oc1..testresource"
    user.compartment_id = "ocid1.tenancy.oc1..test"
    user.lifecycle_state = "ACTIVE"
    user.freeform_tags = {}
    user.defined_tags = {}
    return user


@pytest.fixture
def user_create_args(module_args):
    """Module args for creating a user."""
    module_args.update({
        "compartment_id": 'ocid1.tenancy.oc1..test',
        "name": 'test-user',
        "description": 'Test user',
        "email": 'test@example.com',
        "user_id": None,
    })
    return module_args


class TestOciUserCreate:
    """Test user creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_user(self, mock_create_client, user_create_args):
        """Creating a user calls create_user."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_user()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_user.return_value = mock_response

        module = MagicMock()
        module.params = user_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_user import create_resource
        result = create_resource(mock_client, module)

        mock_client.create_user.assert_called_once()


class TestOciUserDelete:
    """Test user deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_user(self, mock_create_client, module_args):
        """Deleting a user calls delete_user."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "user_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "email": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_user()

        from ansible_collections.oracle.oci.plugins.modules.oci_user import delete_resource
        delete_resource(mock_client, module, resource)

        mock_client.delete_user.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_user_already_gone(self, mock_create_client, module_args):
        """When user does not exist, get returns None via ServiceError 404."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_user.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "user_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "email": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_user import get_existing_resource
        result = get_existing_resource(mock_client, module)
        assert result is None


class TestOciUserUpdate:
    """Test user update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_user(self, mock_create_client, module_args):
        """Updating a user calls update_user."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "user_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "email": None,
            "description": "Updated description",
        })

        updated = _build_user(name="updated-user")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_user.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_user()

        from ansible_collections.oracle.oci.plugins.modules.oci_user import update_resource
        result = update_resource(mock_client, module, resource)

        mock_client.update_user.assert_called_once()


class TestOciUserIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test-user',
            "description": 'Test user',
            "email": 'test@example.com',
            "compartment_id": None,
            "user_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_user()

        from ansible_collections.oracle.oci.plugins.modules.oci_user import needs_update
        assert not needs_update(module, resource)
