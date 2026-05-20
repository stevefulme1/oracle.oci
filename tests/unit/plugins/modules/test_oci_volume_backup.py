"""Unit tests for oracle.oci.oci_volume_backup module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_volume_backup"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_volume_backup(
    display_name='test-backup',
):
    """Return a mock OCI volume_backup object."""
    volume_backup = MagicMock()
    volume_backup.display_name = 'test-backup'
    volume_backup.id = "ocid1.test.oc1..testresource"
    volume_backup.compartment_id = "ocid1.compartment.oc1..test"
    volume_backup.lifecycle_state = "AVAILABLE"
    volume_backup.freeform_tags = {}
    volume_backup.defined_tags = {}
    return volume_backup


@pytest.fixture
def volume_backup_create_args(module_args):
    """Module args for creating a volume_backup."""
    module_args.update({
        "volume_id": 'ocid1.volume.oc1..test',
        "display_name": 'test-backup',
        "type": 'FULL',
        "compartment_id": None,
    })
    return module_args


class TestOciVolumeBackupCreate:
    """Test volume_backup creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_volume_backup(self, mock_create_client, volume_backup_create_args):
        """Creating a volume_backup calls create_volume_backup."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_volume_backup()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_volume_backup.return_value = mock_response

        module = MagicMock()
        module.params = volume_backup_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume_backup import OciVolumeBackup
        obj = OciVolumeBackup(module)
        result = obj.create_resource()

        mock_client.create_volume_backup.assert_called_once()


class TestOciVolumeBackupDelete:
    """Test volume_backup deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_volume_backup(self, mock_create_client, module_args):
        """Deleting a volume_backup calls delete_volume_backup."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "volume_backup_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "volume_id": None,
            "display_name": None,
            "type": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume_backup import OciVolumeBackup
        resource = _build_volume_backup()

        obj = OciVolumeBackup(module)
        obj.delete_resource(resource)

        mock_client.delete_volume_backup.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_volume_backup_already_gone(self, mock_create_client, module_args):
        """When volume_backup does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_volume_backup.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "volume_backup_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "volume_id": None,
            "display_name": None,
            "type": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume_backup import OciVolumeBackup
        obj = OciVolumeBackup(module)
        result = obj.get_resource()
        assert result is None


class TestOciVolumeBackupUpdate:
    """Test volume_backup update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_volume_backup(self, mock_create_client, module_args):
        """Updating a volume_backup calls update_volume_backup."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "volume_backup_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "volume_id": None,
            "display_name": None,
            "type": None,
            "display_name": "updated-volume_backup",
        })

        updated = _build_volume_backup(display_name="updated-volume_backup")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_volume_backup.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume_backup import OciVolumeBackup
        resource = _build_volume_backup()

        obj = OciVolumeBackup(module)
        result = obj.update_resource(resource)

        mock_client.update_volume_backup.assert_called_once()


class TestOciVolumeBackupIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-backup',
            "volume_id": None,
            "type": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume_backup import OciVolumeBackup
        resource = _build_volume_backup()

        obj = OciVolumeBackup(module)
        assert not obj.needs_update(resource)
