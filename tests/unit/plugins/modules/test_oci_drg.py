"""Unit tests for oracle.oci.oci_drg module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_drg"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_drg(
    display_name='test-drg',
):
    """Return a mock OCI drg object."""
    drg = MagicMock()
    drg.display_name = 'test-drg'
    drg.id = "ocid1.test.oc1..testresource"
    drg.compartment_id = "ocid1.compartment.oc1..test"
    drg.lifecycle_state = "AVAILABLE"
    drg.freeform_tags = {}
    drg.defined_tags = {}
    return drg


@pytest.fixture
def drg_create_args(module_args):
    """Module args for creating a drg."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "display_name": 'test-drg',
    })
    return module_args


class TestOciDrgCreate:
    """Test drg creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_drg(self, mock_create_client, drg_create_args):
        """Creating a drg calls create_drg."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_drg()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_drg.return_value = mock_response

        module = MagicMock()
        module.params = drg_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_drg import OciDrg
        obj = OciDrg(module)
        result = obj.create_resource()

        mock_client.create_drg.assert_called_once()


class TestOciDrgDelete:
    """Test drg deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_drg(self, mock_create_client, module_args):
        """Deleting a drg calls delete_drg."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "drg_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_drg import OciDrg
        resource = _build_drg()

        obj = OciDrg(module)
        obj.delete_resource(resource)

        mock_client.delete_drg.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_drg_already_gone(self, mock_create_client, module_args):
        """When drg does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_drg.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "drg_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_drg import OciDrg
        obj = OciDrg(module)
        result = obj.get_resource()
        assert result is None


class TestOciDrgUpdate:
    """Test drg update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_drg(self, mock_create_client, module_args):
        """Updating a drg calls update_drg."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "drg_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "display_name": None,
            "display_name": "updated-drg",
        })

        updated = _build_drg(display_name="updated-drg")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_drg.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_drg import OciDrg
        resource = _build_drg()

        obj = OciDrg(module)
        result = obj.update_resource(resource)

        mock_client.update_drg.assert_called_once()


class TestOciDrgIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-drg',
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_drg import OciDrg
        resource = _build_drg()

        obj = OciDrg(module)
        assert not obj.needs_update(resource)
