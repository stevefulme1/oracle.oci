"""Unit tests for oracle.oci.oci_image module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_image"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_image(
    display_name='test-image',
):
    """Return a mock OCI image object."""
    image = MagicMock()
    image.display_name = 'test-image'
    image.id = "ocid1.test.oc1..testresource"
    image.compartment_id = "ocid1.compartment.oc1..test"
    image.lifecycle_state = "AVAILABLE"
    image.freeform_tags = {}
    image.defined_tags = {}
    return image


@pytest.fixture
def image_create_args(module_args):
    """Module args for creating a image."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "instance_id": 'ocid1.instance.oc1..test',
        "display_name": 'test-image',
    })
    return module_args


class TestOciImageCreate:
    """Test image creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_image(self, mock_create_client, image_create_args):
        """Creating a image calls create_image."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_image()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_image.return_value = mock_response

        module = MagicMock()
        module.params = image_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_image import OciImage
        obj = OciImage(module)
        result = obj.create_resource()

        mock_client.create_image.assert_called_once()


class TestOciImageDelete:
    """Test image deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_image(self, mock_create_client, module_args):
        """Deleting a image calls delete_image."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "image_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "instance_id": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_image import OciImage
        resource = _build_image()

        obj = OciImage(module)
        obj.delete_resource(resource)

        mock_client.delete_image.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_image_already_gone(self, mock_create_client, module_args):
        """When image does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_image.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "image_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "instance_id": None,
            "display_name": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_image import OciImage
        obj = OciImage(module)
        result = obj.get_resource()
        assert result is None


class TestOciImageUpdate:
    """Test image update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_image(self, mock_create_client, module_args):
        """Updating a image calls update_image."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "image_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "instance_id": None,
            "display_name": None,
            "display_name": "updated-image",
        })

        updated = _build_image(display_name="updated-image")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_image.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_image import OciImage
        resource = _build_image()

        obj = OciImage(module)
        result = obj.update_resource(resource)

        mock_client.update_image.assert_called_once()


class TestOciImageIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "display_name": 'test-image',
            "instance_id": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_image import OciImage
        resource = _build_image()

        obj = OciImage(module)
        assert not obj.needs_update(resource)
