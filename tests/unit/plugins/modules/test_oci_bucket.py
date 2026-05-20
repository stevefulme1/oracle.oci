"""Unit tests for oracle.oci.oci_bucket module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_bucket"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_bucket(
    name="test-bucket",
    namespace_name="testnamespace",
    compartment_id="ocid1.compartment.oc1..test",
    public_access_type="NoPublicAccess",
    storage_tier="Standard",
):
    """Return a mock OCI bucket object."""
    bucket = MagicMock()
    bucket.name = name
    bucket.namespace = namespace_name
    bucket.compartment_id = compartment_id
    bucket.public_access_type = public_access_type
    bucket.storage_tier = storage_tier
    bucket.freeform_tags = {}
    bucket.defined_tags = {}
    return bucket


@pytest.fixture
def bucket_create_args(module_args):
    """Module args for creating a bucket."""
    module_args.update({
        "namespace_name": "testnamespace",
        "name": "test-bucket",
        "compartment_id": "ocid1.compartment.oc1..test",
        "public_access_type": "NoPublicAccess",
        "storage_tier": "Standard",
    })
    return module_args


class TestOciBucketCreate:
    """Test bucket creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_bucket(self, mock_create_client, bucket_create_args):
        """Creating a bucket calls create_bucket."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created_bucket = _build_bucket()
        mock_response = MagicMock()
        mock_response.data = created_bucket
        mock_client.create_bucket.return_value = mock_response

        module = MagicMock()
        module.params = bucket_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_bucket import OciBucket
        oci_bucket = OciBucket(module)
        result = oci_bucket.create_resource()

        mock_client.create_bucket.assert_called_once()
        assert mock_client.create_bucket.call_args[0][0] == "testnamespace"
        create_details = mock_client.create_bucket.call_args[0][1]
        assert create_details.name == "test-bucket"
        assert create_details.compartment_id == "ocid1.compartment.oc1..test"
        assert result.name == "test-bucket"

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_bucket_with_public_access(self, mock_create_client, bucket_create_args):
        """Public access type is passed through to create details."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        bucket_create_args["public_access_type"] = "ObjectRead"

        mock_response = MagicMock()
        mock_response.data = _build_bucket(public_access_type="ObjectRead")
        mock_client.create_bucket.return_value = mock_response

        module = MagicMock()
        module.params = bucket_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_bucket import OciBucket
        oci_bucket = OciBucket(module)
        oci_bucket.create_resource()

        create_details = mock_client.create_bucket.call_args[0][1]
        assert create_details.public_access_type == "ObjectRead"


class TestOciBucketDelete:
    """Test bucket deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_bucket(self, mock_create_client, module_args):
        """Deleting a bucket calls delete_bucket."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "namespace_name": "testnamespace",
            "name": "test-bucket",
            "state": "absent",
            "compartment_id": None,
            "public_access_type": None,
            "storage_tier": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_bucket import OciBucket
        resource = _build_bucket()

        oci_bucket = OciBucket(module)
        oci_bucket.delete_resource(resource)

        mock_client.delete_bucket.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_bucket_already_gone(self, mock_create_client, module_args):
        """When bucket does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_bucket.side_effect = oci.exceptions.ServiceError(
            status=404, code="BucketNotFound", message="not found", headers={},
        )

        module_args.update({
            "namespace_name": "testnamespace",
            "name": "nonexistent-bucket",
            "state": "absent",
            "compartment_id": None,
            "public_access_type": None,
            "storage_tier": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_bucket import OciBucket
        oci_bucket = OciBucket(module)
        result = oci_bucket.get_resource()
        assert result is None


class TestOciBucketUpdate:
    """Test bucket update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_public_access(self, mock_create_client, module_args):
        """Updating public_access_type calls update_bucket."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "namespace_name": "testnamespace",
            "name": "test-bucket",
            "compartment_id": None,
            "public_access_type": "ObjectRead",
            "storage_tier": None,
        })

        updated_bucket = _build_bucket(public_access_type="ObjectRead")
        mock_response = MagicMock()
        mock_response.data = updated_bucket
        mock_client.update_bucket.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_bucket import OciBucket
        resource = _build_bucket(public_access_type="NoPublicAccess")

        oci_bucket = OciBucket(module)
        result = oci_bucket.update_resource(resource)

        mock_client.update_bucket.assert_called_once()
        assert result.public_access_type == "ObjectRead"


class TestOciBucketIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "namespace_name": "testnamespace",
            "name": "test-bucket",
            "compartment_id": None,
            "public_access_type": "NoPublicAccess",
            "storage_tier": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_bucket import OciBucket
        resource = _build_bucket(public_access_type="NoPublicAccess")

        oci_bucket = OciBucket(module)
        assert not oci_bucket.needs_update(resource)
