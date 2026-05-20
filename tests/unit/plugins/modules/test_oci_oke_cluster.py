"""Unit tests for oracle.oci.oci_oke_cluster module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_oke_cluster"
AUTH_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth"
RESOURCE_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_resource"
WAIT_PATH = "ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait"


def _build_oke_cluster(
    name='test-cluster',
    kubernetes_version='v1.28.0',
):
    """Return a mock OCI oke_cluster object."""
    oke_cluster = MagicMock()
    oke_cluster.name = 'test-cluster'
    oke_cluster.kubernetes_version = 'v1.28.0'
    oke_cluster.id = "ocid1.test.oc1..testresource"
    oke_cluster.compartment_id = "ocid1.compartment.oc1..test"
    oke_cluster.lifecycle_state = "AVAILABLE"
    oke_cluster.freeform_tags = {}
    oke_cluster.defined_tags = {}
    return oke_cluster


@pytest.fixture
def oke_cluster_create_args(module_args):
    """Module args for creating a oke_cluster."""
    module_args.update({
        "compartment_id": 'ocid1.compartment.oc1..test',
        "name": 'test-cluster',
        "vcn_id": 'ocid1.vcn.oc1..test',
        "kubernetes_version": 'v1.28.0',
        "options": None,
    })
    return module_args


class TestOciOkeClusterCreate:
    """Test oke_cluster creation."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_create_oke_cluster(self, mock_create_client, oke_cluster_create_args):
        """Creating a oke_cluster calls create_cluster."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        created = _build_oke_cluster()
        mock_response = MagicMock()
        mock_response.data = created
        mock_client.create_cluster.return_value = mock_response

        module = MagicMock()
        module.params = oke_cluster_create_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_oke_cluster import OciOkeCluster
        obj = OciOkeCluster(module)
        result = obj.create_resource()

        mock_client.create_cluster.assert_called_once()


class TestOciOkeClusterDelete:
    """Test oke_cluster deletion."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_oke_cluster(self, mock_create_client, module_args):
        """Deleting a oke_cluster calls delete_cluster."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "cluster_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "name": None,
            "vcn_id": None,
            "kubernetes_version": None,
            "options": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_oke_cluster import OciOkeCluster
        resource = _build_oke_cluster()

        obj = OciOkeCluster(module)
        obj.delete_resource(resource)

        mock_client.delete_cluster.assert_called_once()

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_delete_oke_cluster_already_gone(self, mock_create_client, module_args):
        """When oke_cluster does not exist, get_resource returns None."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        import oci.exceptions
        mock_client.get_cluster.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotAuthorizedOrNotFound", message="not found", headers={},
        )

        module_args.update({
            "cluster_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "name": None,
            "vcn_id": None,
            "kubernetes_version": None,
            "options": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_oke_cluster import OciOkeCluster
        obj = OciOkeCluster(module)
        result = obj.get_resource()
        assert result is None


class TestOciOkeClusterUpdate:
    """Test oke_cluster update."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_update_oke_cluster(self, mock_create_client, module_args):
        """Updating a oke_cluster calls update_cluster."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "cluster_id": "ocid1.test.oc1..testresource",
            "state": "absent",
            "name": None,
            "vcn_id": None,
            "kubernetes_version": None,
            "options": None,
            "name": "updated-oke_cluster",
        })

        updated = _build_oke_cluster(name="updated-oke_cluster")
        mock_response = MagicMock()
        mock_response.data = updated
        mock_client.update_cluster.return_value = mock_response

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_oke_cluster import OciOkeCluster
        resource = _build_oke_cluster()

        obj = OciOkeCluster(module)
        result = obj.update_resource(resource)

        mock_client.update_cluster.assert_called_once()


class TestOciOkeClusterIdempotent:
    """Test idempotent behavior when no change is needed."""

    @patch(f"{RESOURCE_PATH}.create_service_client")
    def test_no_change_needed(self, mock_create_client, module_args):
        """When current state matches desired state, needs_update returns False."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        module_args.update({
            "name": 'test-cluster',
            "kubernetes_version": 'v1.28.0',
            "vcn_id": None,
            "options": None,
            "compartment_id": None,
        })

        module = MagicMock()
        module.params = module_args
        module.check_mode = False
        module.params["wait"] = False

        from ansible_collections.oracle.oci.plugins.modules.oci_oke_cluster import OciOkeCluster
        resource = _build_oke_cluster()

        obj = OciOkeCluster(module)
        assert not obj.needs_update(resource)
