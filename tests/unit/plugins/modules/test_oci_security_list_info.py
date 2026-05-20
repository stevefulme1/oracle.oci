"""Unit tests for oracle.oci.oci_security_list_info module."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest

import oci.exceptions

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import to_dict as _real_to_dict

# Ensure to_dict is available in the module namespace even when the
# stevefulme1.oci_cloud import path is not registered.
import ansible_collections.oracle.oci.plugins.modules.oci_security_list_info as _target_module
if not hasattr(_target_module, "to_dict"):
    _target_module.to_dict = _real_to_dict


MODULE_PATH = "ansible_collections.oracle.oci.plugins.modules.oci_security_list_info"


def _mock_resource(display_name="test-resource", resource_id="ocid1.security_list.oc1..test"):
    """Return a mock OCI security_list object."""
    resource = MagicMock()
    resource.display_name = display_name
    resource.id = resource_id
    resource.lifecycle_state = "AVAILABLE"
    resource.compartment_id = "ocid1.compartment.oc1..test"
    return resource


@pytest.fixture
def info_module_args(module_args):
    """Module args for info queries."""
    module_args.update({
        "compartment_id": "ocid1.compartment.oc1..test",
        "security_list_id": None,
        "limit": 1000,
        "page": None,
        "max_results": 1000,
    })
    return module_args


class TestGetOciSecurityListInfo:
    """Test retrieving a single security_list by ID."""

    def test_get_resource_by_id(self, info_module_args):
        """get_security_list() returns a single resource wrapped in a list."""
        mock_client = MagicMock()

        resource = _mock_resource()
        mock_response = MagicMock()
        mock_response.data = resource
        mock_client.get_security_list.return_value = mock_response

        info_module_args["security_list_id"] = "ocid1.security_list.oc1..test"

        module = MagicMock()
        module.params = info_module_args

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list_info import get_resource
        result = get_resource(mock_client, module)

        mock_client.get_security_list.assert_called_once_with("ocid1.security_list.oc1..test")
        assert len(result) == 1

    def test_get_resource_404_returns_empty(self, info_module_args):
        """ServiceError 404 returns an empty list."""
        mock_client = MagicMock()

        mock_client.get_security_list.side_effect = oci.exceptions.ServiceError(
            status=404, code="NotFound", message="not found", headers={},
        )

        info_module_args["security_list_id"] = "ocid1.security_list.oc1..gone"

        module = MagicMock()
        module.params = info_module_args

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list_info import get_resource
        result = get_resource(mock_client, module)

        assert result == []

    def test_get_resource_non_404_fails(self, info_module_args):
        """Non-404 ServiceError calls module.fail_json."""
        mock_client = MagicMock()

        mock_client.get_security_list.side_effect = oci.exceptions.ServiceError(
            status=500, code="InternalError", message="server error", headers={},
        )

        info_module_args["security_list_id"] = "ocid1.security_list.oc1..bad"

        module = MagicMock()
        module.params = info_module_args

        from ansible_collections.oracle.oci.plugins.modules.oci_security_list_info import get_resource
        get_resource(mock_client, module)

        module.fail_json.assert_called_once()


class TestListOciSecurityListInfo:
    """Test listing security_lists by compartment."""

    def test_list_resources(self, info_module_args):
        """list_security_lists() returns resources in the compartment."""
        mock_client = MagicMock()

        resources = [_mock_resource(display_name=f"res-{i}") for i in range(3)]
        mock_pagination_response = MagicMock()
        mock_pagination_response.data = resources

        module = MagicMock()
        module.params = info_module_args

        with patch("oci.pagination.list_call_get_all_results", return_value=mock_pagination_response):
            from ansible_collections.oracle.oci.plugins.modules.oci_security_list_info import list_resources
            result = list_resources(mock_client, module)

        assert len(result) == 3

    def test_list_resources_service_error(self, info_module_args):
        """ServiceError during list calls module.fail_json."""
        mock_client = MagicMock()

        module = MagicMock()
        module.params = info_module_args

        with patch(
            "oci.pagination.list_call_get_all_results",
            side_effect=oci.exceptions.ServiceError(
                status=403, code="NotAuthorized", message="forbidden", headers={},
            ),
        ):
            from ansible_collections.oracle.oci.plugins.modules.oci_security_list_info import list_resources
            list_resources(mock_client, module)

        module.fail_json.assert_called_once()

    def test_list_empty_compartment(self, info_module_args):
        """Empty compartment returns an empty list."""
        mock_client = MagicMock()

        mock_pagination_response = MagicMock()
        mock_pagination_response.data = []

        module = MagicMock()
        module.params = info_module_args

        with patch("oci.pagination.list_call_get_all_results", return_value=mock_pagination_response):
            from ansible_collections.oracle.oci.plugins.modules.oci_security_list_info import list_resources
            result = list_resources(mock_client, module)

        assert result == []
