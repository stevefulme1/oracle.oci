"""Unit tests for oracle.oci.plugins.module_utils.oci_auth."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
from unittest.mock import MagicMock, patch


AUTH_PATH = "ansible_collections.oracle.oci.plugins.module_utils.oci_auth"


class TestGetOciConfig:
    """Test config file parsing and env var overrides."""

    @patch(f"{AUTH_PATH}.oci")
    def test_config_from_file(self, mock_oci):
        """Config is loaded from the default OCI config file."""
        mock_oci.config.from_file.return_value = {
            "tenancy": "ocid1.tenancy.oc1..fromfile",
            "user": "ocid1.user.oc1..fromfile",
            "region": "us-ashburn-1",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "/home/user/.oci/key.pem",
        }

        module = MagicMock()
        module.params = {
            "auth_type": "api_key",
            "config_file_location": "~/.oci/config",
            "config_profile_name": "DEFAULT",
            "tenancy": None,
            "api_user": None,
            "region": None,
            "api_user_fingerprint": None,
            "api_user_key_file": None,
            "api_user_key_pass_phrase": None,
        }

        with patch("os.path.isfile", return_value=True):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import get_oci_config
            config = get_oci_config(module)

        mock_oci.config.from_file.assert_called_once()
        assert config["tenancy"] == "ocid1.tenancy.oc1..fromfile"
        assert config["region"] == "us-ashburn-1"

    @patch(f"{AUTH_PATH}.oci")
    def test_env_var_override(self, mock_oci):
        """Environment variables override config file values."""
        mock_oci.config.from_file.return_value = {
            "tenancy": "ocid1.tenancy.oc1..fromfile",
            "user": "ocid1.user.oc1..fromfile",
            "region": "us-ashburn-1",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "/home/user/.oci/key.pem",
        }

        module = MagicMock()
        module.params = {
            "auth_type": "api_key",
            "config_file_location": "~/.oci/config",
            "config_profile_name": "DEFAULT",
            "tenancy": None,
            "api_user": None,
            "region": None,
            "api_user_fingerprint": None,
            "api_user_key_file": None,
            "api_user_key_pass_phrase": None,
        }

        env_overrides = {
            "OCI_REGION": "eu-frankfurt-1",
            "OCI_TENANCY_ID": "ocid1.tenancy.oc1..fromenv",
        }

        with patch("os.path.isfile", return_value=True), \
             patch.dict(os.environ, env_overrides, clear=False):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import get_oci_config
            config = get_oci_config(module)

        assert config["region"] == "eu-frankfurt-1"
        assert config["tenancy"] == "ocid1.tenancy.oc1..fromenv"

    @patch(f"{AUTH_PATH}.oci")
    def test_module_params_take_precedence(self, mock_oci):
        """Explicit module params override both config file and env vars."""
        mock_oci.config.from_file.return_value = {
            "region": "us-ashburn-1",
        }

        module = MagicMock()
        module.params = {
            "auth_type": "api_key",
            "config_file_location": "~/.oci/config",
            "config_profile_name": "DEFAULT",
            "tenancy": "ocid1.tenancy.oc1..fromparam",
            "api_user": None,
            "region": "ap-tokyo-1",
            "api_user_fingerprint": None,
            "api_user_key_file": None,
            "api_user_key_pass_phrase": None,
        }

        with patch("os.path.isfile", return_value=True):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import get_oci_config
            config = get_oci_config(module)

        assert config["region"] == "ap-tokyo-1"
        assert config["tenancy"] == "ocid1.tenancy.oc1..fromparam"

    def test_instance_principal_returns_minimal_config(self):
        """Instance principal auth returns only the auth_type."""
        module = MagicMock()
        module.params = {
            "auth_type": "instance_principal",
            "config_file_location": None,
            "config_profile_name": None,
        }

        from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import get_oci_config
        config = get_oci_config(module)
        assert config == {"auth_type": "instance_principal"}

    def test_resource_principal_returns_minimal_config(self):
        """Resource principal auth returns only the auth_type."""
        module = MagicMock()
        module.params = {
            "auth_type": "resource_principal",
            "config_file_location": None,
            "config_profile_name": None,
        }

        from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import get_oci_config
        config = get_oci_config(module)
        assert config == {"auth_type": "resource_principal"}


class TestCreateServiceClient:
    """Test service client creation for different auth methods."""

    @patch(f"{AUTH_PATH}.oci")
    def test_instance_principal_client(self, mock_oci):
        """Instance principal creates client with IP signer."""
        mock_signer = MagicMock()
        mock_oci.auth.signers.InstancePrincipalsSecurityTokenSigner.return_value = mock_signer
        mock_oci.config.from_file = MagicMock()

        mock_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        module = MagicMock()
        module.params = {"auth_type": "instance_principal"}

        # Patch HAS_OCI_SDK to True
        with patch(f"{AUTH_PATH}.HAS_OCI_SDK", True):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
            client = create_service_client(module, mock_client_class)

        mock_oci.auth.signers.InstancePrincipalsSecurityTokenSigner.assert_called_once()
        mock_client_class.assert_called_once_with(config={}, signer=mock_signer)
        assert client == mock_client_instance

    @patch(f"{AUTH_PATH}.oci")
    def test_resource_principal_client(self, mock_oci):
        """Resource principal creates client with RP signer."""
        mock_signer = MagicMock()
        mock_oci.auth.signers.get_resource_principals_signer.return_value = mock_signer

        mock_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        module = MagicMock()
        module.params = {"auth_type": "resource_principal"}

        with patch(f"{AUTH_PATH}.HAS_OCI_SDK", True):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
            client = create_service_client(module, mock_client_class)

        mock_oci.auth.signers.get_resource_principals_signer.assert_called_once()
        mock_client_class.assert_called_once_with(config={}, signer=mock_signer)
        assert client == mock_client_instance

    @patch(f"{AUTH_PATH}.oci")
    def test_api_key_client(self, mock_oci):
        """API key auth creates client with validated config."""
        test_config = {
            "tenancy": "ocid1.tenancy.oc1..test",
            "user": "ocid1.user.oc1..test",
            "region": "us-phoenix-1",
            "fingerprint": "aa:bb:cc:dd",
            "key_file": "/tmp/key.pem",
        }
        mock_oci.config.from_file.return_value = test_config.copy()

        mock_client_class = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance

        module = MagicMock()
        module.params = {
            "auth_type": "api_key",
            "config_file_location": "~/.oci/config",
            "config_profile_name": "DEFAULT",
            "tenancy": None,
            "api_user": None,
            "region": None,
            "api_user_fingerprint": None,
            "api_user_key_file": None,
            "api_user_key_pass_phrase": None,
        }

        with patch(f"{AUTH_PATH}.HAS_OCI_SDK", True), \
             patch("os.path.isfile", return_value=True):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
            client = create_service_client(module, mock_client_class)

        mock_oci.config.validate_config.assert_called_once()
        assert client == mock_client_instance

    def test_missing_sdk_fails(self):
        """Missing OCI SDK causes fail_json."""
        mock_client_class = MagicMock()
        module = MagicMock()
        module.params = {"auth_type": "api_key"}

        with patch(f"{AUTH_PATH}.HAS_OCI_SDK", False):
            from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
            create_service_client(module, mock_client_class)

        module.fail_json.assert_called_once()
        assert "oci" in module.fail_json.call_args[1]["msg"].lower()
