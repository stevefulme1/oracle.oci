"""Unit tests for oracle.oci.oci_boot_volume module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_boot_volume"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_boot_volume(
    display_name='test-boot-vol',
):
    """Return a mock OCI boot_volume object."""
    boot_volume = MagicMock()
    boot_volume.display_name = 'test-boot-vol'
    boot_volume.id = "ocid1.test.oc1..testresource"
    boot_volume.compartment_id = "ocid1.compartment.oc1..test"
    boot_volume.lifecycle_state = "AVAILABLE"
    boot_volume.freeform_tags = {}
    boot_volume.defined_tags = {}
    return boot_volume


@pytest.fixture
def boot_volume_create_args(module_args):
    """Module args for creating a boot_volume."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "availability_domain": 'Uocm:PHX-AD-1',
        "display_name": 'test-boot-vol',
        "source_details": {'type': 'bootVolume', 'id': 'ocid1.bootvolume.oc1..test'},
        "size_in_gbs": None,
        "vpus_per_gb": None,
    })
    return module_args


class TestOciBootVolumeCreate:
    """Test boot_volume creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_boot_volume(self, mock_create_client, boot_volume_create_args):
        """Creating a boot_volume calls create_boot_volume."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_boot_volume()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_boot_volume.return_value = mock_response

        module = MagicMock()
        module.params = boot_volume_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_boot_volume import OciBootVolume
        obj = OciBootVolume(module)
        result = obj.create_resource()

        mock_client.create_boot_volume.assert_called_once()


class TestOciBootVolumeDelete:
    """Test boot_volume deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_boot_volume(self, mock_create_client, module_args):
        """Deleting a boot_volume calls delete_boot_volume."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "boot_volume_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "source_details": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_boot_volume import OciBootVolume
        resource = _build_boot_volume()

        obj = OciBootVolume(module)
        obj.delete_resource(resource)

        mock_client.delete_boot_volume.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_boot_volume_already_gone(self, mock_create_client, module_args):
        """When boot_volume does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_boot_volume.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "boot_volume_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "source_details": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_boot_volume import OciBootVolume
        obj = OciBootVolume(module)
        result = obj.get_resource()
        assert result is None


class TestOciBootVolumeUpdate:
    """Test boot_volume update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_boot_volume(self, mock_create_client, module_args):
        """Updating a boot_volume calls update_boot_volume."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "boot_volume_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "source_details": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
            "display_name": "updated-boot_volume",
        })

        updated = _build_boot_volume(display_name="updated-boot_volume")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_boot_volume.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_boot_volume import OciBootVolume
        resource = _build_boot_volume()

        obj = OciBootVolume(module)
        result = obj.update_resource(resource)

        mock_client.update_boot_volume.assert_called_once()


class TestOciBootVolumeIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-boot-vol',
            "availability_domain": None,
            "source_details": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_boot_volume import OciBootVolume
        resource = _build_boot_volume()

        obj = OciBootVolume(module)
        assert not obj.needs_update(resource)
