"""Unit tests for oracle.oci.oci_policy module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_policy"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_policy(
    name='test-policy',
    description='Test policy',
    statements=['Allow group test-group to manage all-resources in tenancy'],
):
    """Return a mock OCI policy object."""
    policy = MagicMock()
    policy.name = 'test-policy'
    policy.description = 'Test policy'
    policy.statements = ['Allow group test-group to manage all-resources in tenancy']
    policy.id = "ocid1.test.oc1..testresource"
    policy.compartment_id = "ocid1.tenancy.oc1..test"
    policy.lifecycle_state = "ACTIVE"
    policy.freeform_tags = {}
    policy.defined_tags = {}
    return policy


@pytest.fixture
def policy_create_args(module_args):
    """Module args for creating a policy."""
    module_args.update({
        "compartment_id": 'ocid1.tenancy.oc1..test',
        "name": 'test-policy',
        "description": 'Test policy',
        "statements": ['Allow group test-group to manage all-resources in tenancy'],
        "policy_id": None,
    })
    return module_args


class TestOciPolicyCreate:
    """Test policy creation."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_create_policy(self, mock_create_client, policy_create_args):
        """Creating a policy calls create_policy."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_policy()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_policy.return_value = mock_response

        module = MagicMock()
        module.params = policy_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_policy import create_resource
        result = create_resource(mock_client, module)

        mock_client.create_policy.assert_called_once()


class TestOciPolicyDelete:
    """Test policy deletion."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_policy(self, mock_create_client, module_args):
        """Deleting a policy calls delete_policy."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "policy_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "statements": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_policy()

        from ansible_collections.oracle.oci.plugins.modules.oci_policy import delete_resource
        delete_resource(mock_client, module, resource)

        mock_client.delete_policy.assert_called_once()

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_delete_policy_already_gone(self, mock_create_client, module_args):
        """When policy does not exist, get returns None via ServiceError 404."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_policy.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "policy_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "statements": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_policy import get_existing_resource
        result = get_existing_resource(mock_client, module)
        assert result is None


class TestOciPolicyUpdate:
    """Test policy update."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_update_policy(self, mock_create_client, module_args):
        """Updating a policy calls update_policy."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "policy_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "compartment_id": None,
            "name": None,
            "description": None,
            "statements": None,
            "description": "Updated description",
        })

        updated = _build_policy(name="updated-policy")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_policy.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_policy()

        from ansible_collections.oracle.oci.plugins.modules.oci_policy import update_resource
        result = update_resource(mock_client, module, resource)

        mock_client.update_policy.assert_called_once()


class TestOciPolicyIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{AUTH_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test-policy',
            "description": 'Test policy',
            "statements": ['Allow group test-group to manage all-resources in tenancy'],
            "compartment_id": None,
            "policy_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        resource = _build_policy()

        from ansible_collections.oracle.oci.plugins.modules.oci_policy import needs_update
        assert not needs_update(module, resource)
