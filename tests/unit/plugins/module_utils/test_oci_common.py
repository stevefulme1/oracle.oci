"""Unit tests for oracle.oci.plugins.module_utils.oci_common."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock

import pytest


class TestOciCommonArgs:
    """Test OCI_COMMON_ARGS argument spec."""

    def test_common_args_is_dict(self):
        """OCI_COMMON_ARGS is a dict."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        assert isinstance(OCI_COMMON_ARGS, dict)

    def test_contains_auth_params(self):
        """OCI_COMMON_ARGS includes authentication parameters."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        expected_keys = [
            "config_file_location",
            "config_profile_name",
            "auth_type",
            "tenancy",
            "region",
            "api_user",
            "api_user_fingerprint",
            "api_user_key_file",
            "api_user_key_pass_phrase",
        ]
        for key in expected_keys:
            assert key in OCI_COMMON_ARGS, f"Missing auth param: {key}"

    def test_contains_wait_params(self):
        """OCI_COMMON_ARGS includes wait parameters."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        assert "wait" in OCI_COMMON_ARGS
        assert "wait_timeout" in OCI_COMMON_ARGS
        assert "wait_interval" in OCI_COMMON_ARGS

    def test_contains_tag_params(self):
        """OCI_COMMON_ARGS includes tagging parameters."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        assert "freeform_tags" in OCI_COMMON_ARGS
        assert "defined_tags" in OCI_COMMON_ARGS

    def test_auth_type_choices(self):
        """auth_type has the expected choices."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        choices = OCI_COMMON_ARGS["auth_type"]["choices"]
        assert "api_key" in choices
        assert "instance_principal" in choices
        assert "resource_principal" in choices
        assert "session_token" in choices

    def test_default_values(self):
        """Key parameters have correct defaults."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        assert OCI_COMMON_ARGS["config_file_location"]["default"] == "~/.oci/config"
        assert OCI_COMMON_ARGS["config_profile_name"]["default"] == "DEFAULT"
        assert OCI_COMMON_ARGS["auth_type"]["default"] == "api_key"
        assert OCI_COMMON_ARGS["wait"]["default"] is True
        assert OCI_COMMON_ARGS["wait_timeout"]["default"] == 1200
        assert OCI_COMMON_ARGS["wait_interval"]["default"] == 30

    def test_no_log_fields(self):
        """Sensitive fields are marked no_log."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import OCI_COMMON_ARGS
        assert OCI_COMMON_ARGS["api_user_fingerprint"].get("no_log") is True
        assert OCI_COMMON_ARGS["api_user_key_pass_phrase"].get("no_log") is True


class TestLifecycleConstants:
    """Test lifecycle state constants and frozen sets."""

    def test_wait_states(self):
        """WAIT_STATES contains provisioning/creating/deleting/terminating."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import WAIT_STATES
        assert "PROVISIONING" in WAIT_STATES
        assert "CREATING" in WAIT_STATES
        assert "DELETING" in WAIT_STATES
        assert "TERMINATING" in WAIT_STATES

    def test_ready_states(self):
        """READY_STATES contains active/available/running."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import READY_STATES
        assert "ACTIVE" in READY_STATES
        assert "AVAILABLE" in READY_STATES
        assert "RUNNING" in READY_STATES

    def test_dead_states(self):
        """DEAD_STATES contains deleted/terminated."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import DEAD_STATES
        assert "DELETED" in DEAD_STATES
        assert "TERMINATED" in DEAD_STATES

    def test_sets_are_frozen(self):
        """State sets are frozenset (immutable)."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
            WAIT_STATES, READY_STATES, DEAD_STATES,
        )
        assert isinstance(WAIT_STATES, frozenset)
        assert isinstance(READY_STATES, frozenset)
        assert isinstance(DEAD_STATES, frozenset)

    def test_no_overlap_ready_dead(self):
        """READY_STATES and DEAD_STATES do not overlap."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import READY_STATES, DEAD_STATES
        assert READY_STATES.isdisjoint(DEAD_STATES)


class TestToDict:
    """Test to_dict() conversion utility."""

    def test_converts_simple_resource(self):
        """to_dict converts object attributes to dict."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import to_dict

        class FakeResource:
            def __init__(self):
                self.id = "ocid1.test"
                self.name = "test-name"
                self._swagger_types = {"hidden": "str"}

        result = to_dict(FakeResource())
        assert result["id"] == "ocid1.test"
        assert result["name"] == "test-name"
        assert "_swagger_types" not in result

    def test_converts_none(self):
        """to_dict returns empty dict for None."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import to_dict
        assert to_dict(None) == {}

    def test_converts_nested_resource(self):
        """to_dict recursively converts nested objects."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import to_dict

        class Inner:
            def __init__(self):
                self.port = 443

        class Outer:
            def __init__(self):
                self.id = "ocid1.outer"
                self.config = Inner()

        result = to_dict(Outer())
        assert result["id"] == "ocid1.outer"
        assert result["config"]["port"] == 443

    def test_converts_list_of_resources(self):
        """to_dict handles lists containing resource objects."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import to_dict

        class Item:
            def __init__(self, val):
                self.value = val

        class Container:
            def __init__(self):
                self.items = [Item(1), Item(2)]

        result = to_dict(Container())
        assert len(result["items"]) == 2
        assert result["items"][0]["value"] == 1
        assert result["items"][1]["value"] == 2

    def test_passthrough_primitives(self):
        """to_dict returns primitives as-is."""
        from ansible_collections.oracle.oci.plugins.module_utils.oci_common import to_dict
        assert to_dict("hello") == "hello"
        assert to_dict(42) == 42
