"""Unit tests for oracle.oci.oci_volume module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_volume"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_volume(
    display_name='test-volume',
    size_in_gbs=50,
):
    """Return a mock OCI volume object."""
    volume = MagicMock()
    volume.display_name = 'test-volume'
    volume.size_in_gbs = 50
    volume.id = "ocid1.test.oc1..testresource"
    volume.compartment_id = "ocid1.compartment.oc1..test"
    volume.lifecycle_state = "AVAILABLE"
    volume.freeform_tags = {}
    volume.defined_tags = {}
    return volume


@pytest.fixture
def volume_create_args(module_args):
    """Module args for creating a volume."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "availability_domain": 'Uocm:PHX-AD-1',
        "display_name": 'test-volume',
        "size_in_gbs": 50,
        "vpus_per_gb": 10,
    })
    return module_args


class TestOciVolumeCreate:
    """Test volume creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_volume(self, mock_create_client, volume_create_args):
        """Creating a volume calls create_volume."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_volume()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_volume.return_value = mock_response

        module = MagicMock()
        module.params = volume_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume import OciVolume
        obj = OciVolume(module)
        result = obj.create_resource()

        mock_client.create_volume.assert_called_once()


class TestOciVolumeDelete:
    """Test volume deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_volume(self, mock_create_client, module_args):
        """Deleting a volume calls delete_volume."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "volume_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume import OciVolume
        resource = _build_volume()

        obj = OciVolume(module)
        obj.delete_resource(resource)

        mock_client.delete_volume.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_volume_already_gone(self, mock_create_client, module_args):
        """When volume does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_volume.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "volume_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume import OciVolume
        obj = OciVolume(module)
        result = obj.get_resource()
        assert result is None


class TestOciVolumeUpdate:
    """Test volume update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_volume(self, mock_create_client, module_args):
        """Updating a volume calls update_volume."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "volume_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "availability_domain": None,
            "display_name": None,
            "size_in_gbs": None,
            "vpus_per_gb": None,
            "display_name": "updated-volume",
        })

        updated = _build_volume(display_name="updated-volume")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_volume.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume import OciVolume
        resource = _build_volume()

        obj = OciVolume(module)
        result = obj.update_resource(resource)

        mock_client.update_volume.assert_called_once()


class TestOciVolumeIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-volume',
            "size_in_gbs": 50,
            "availability_domain": None,
            "vpus_per_gb": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_volume import OciVolume
        resource = _build_volume()

        obj = OciVolume(module)
        assert not obj.needs_update(resource)
