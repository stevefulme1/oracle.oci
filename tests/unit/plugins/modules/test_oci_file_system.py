"""Unit tests for oracle.oci.oci_file_system module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_file_system"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_file_system(
    display_name='test-fs',
):
    """Return a mock OCI file_system object."""
    file_system = MagicMock()
    file_system.display_name = 'test-fs'
    file_system.id = "ocid1.test.oc1..testresource"
    file_system.compartment_id = "ocid1.compartment.oc1..test"
    file_system.lifecycle_state = "AVAILABLE"
    file_system.freeform_tags = {}
    file_system.defined_tags = {}
    return file_system


@pytest.fixture
def file_system_create_args(module_args):
    """Module args for creating a file_system."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "availability_domain": 'Uocm:PHX-AD-1',
        "display_name": 'test-fs',
    })
    return module_args


class TestOciFileSystemCreate:
    """Test file_system creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_file_system(self, mock_create_client, file_system_create_args):
        """Creating a file_system calls create_file_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_file_system()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_file_system.return_value = mock_response

        module = MagicMock()
        module.params = file_system_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_file_system import OciFileSystem
        obj = OciFileSystem(module)
        result = obj.create_resource()

        mock_client.create_file_system.assert_called_once()


class TestOciFileSystemDelete:
    """Test file_system deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_file_system(self, mock_create_client, module_args):
        """Deleting a file_system calls delete_file_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "file_system_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_file_system import OciFileSystem
        resource = _build_file_system()

        obj = OciFileSystem(module)
        obj.delete_resource(resource)

        mock_client.delete_file_system.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_file_system_already_gone(self, mock_create_client, module_args):
        """When file_system does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_file_system.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "file_system_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_file_system import OciFileSystem
        obj = OciFileSystem(module)
        result = obj.get_resource()
        assert result is None


class TestOciFileSystemUpdate:
    """Test file_system update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_file_system(self, mock_create_client, module_args):
        """Updating a file_system calls update_file_system."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "file_system_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "display_name": "updated-file_system",
        })

        updated = _build_file_system(display_name="updated-file_system")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_file_system.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_file_system import OciFileSystem
        resource = _build_file_system()

        obj = OciFileSystem(module)
        result = obj.update_resource(resource)

        mock_client.update_file_system.assert_called_once()


class TestOciFileSystemIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-fs',
            "availability_domain": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_file_system import OciFileSystem
        resource = _build_file_system()

        obj = OciFileSystem(module)
        assert not obj.needs_update(resource)
