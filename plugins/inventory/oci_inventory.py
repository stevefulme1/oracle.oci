# -*- coding: utf-8 -*-
# Copyright (c) 2026, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
name: oci_inventory
short_description: Oracle Cloud Infrastructure (OCI) dynamic inventory plugin
description:
  - Queries OCI compute instances across regions and compartments to build
    an Ansible dynamic inventory.
  - Automatically groups hosts by region, compartment, availability domain,
    shape, lifecycle state, and freeform tags.
  - Supports tag-based filtering, caching, and multiple authentication methods.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulmer)
extends_documentation_fragment:
  - constructed
  - inventory_cache
options:
  plugin:
    description: Token that ensures this is a source file for the plugin.
    required: true
    choices: ["stevefulme1.oci_cloud.oci_inventory"]
  regions:
    description:
      - List of OCI region identifiers to query.
      - When omitted the plugin queries every region the tenancy is subscribed to.
    type: list
    elements: str
    default: []
  compartments:
    description:
      - List of compartment OCIDs to search for instances.
      - When omitted the plugin searches the tenancy root compartment only.
    type: list
    elements: str
    default: []
  fetch_compute_hosts:
    description:
      - When C(true), compute instances are fetched.
    type: bool
    default: true
  fetch_only_running_hosts:
    description:
      - When false, compute instances in any lifecycle state are fetched (not just RUNNING).
      - Only applies when C(fetch_compute_hosts) is true.
    type: bool
    default: true
  fetch_db_hosts:
    description:
      - When C(true), include Oracle Database system hosts (DB nodes) in the
        inventory in addition to compute instances.
    type: bool
    default: false
  filters:
    description:
      - Dictionary of tag-based filters to limit which instances are included.
      - Keys are tag namespaces (use C(freeform) for freeform tags).
      - Values are dictionaries mapping tag key to the expected tag value.
      - An instance must match B(all) supplied filters.
    type: dict
    default: {}
  hostname_preference:
    description:
      - Ordered list specifying how C(ansible_host) is determined.
      - The first preference that yields a non-empty value wins.
      - Supported values are C(public_ip), C(private_ip), and C(display_name).
    type: list
    elements: str
    default:
      - public_ip
      - private_ip
      - display_name
  config_file:
    description: Path to the OCI SDK configuration file.
    type: str
    default: "~/.oci/config"
  config_profile:
    description: Profile section inside the OCI config file to use.
    type: str
    default: "DEFAULT"
  auth_type:
    description:
      - Authentication mechanism.
      - C(api_key) uses the key defined in the SDK config file.
      - C(instance_principal) authenticates via the instance metadata service.
      - C(resource_principal) authenticates via a resource principal token.
    type: str
    choices:
      - api_key
      - instance_principal
      - resource_principal
    default: api_key
  keyed_groups:
    description: Add hosts to groups based on Jinja2 conditionals and expressions.
  groups:
    description: Add hosts to groups based on Jinja2 conditionals.
  compose:
    description: Create host variables from Jinja2 expressions.

notes:
  - Requires the C(oci) Python SDK (C(pip install oci)).
  - Only instances in the C(RUNNING) lifecycle state are included by default.
    Use C(compose) or C(filters) to customise this behaviour.
  - Inventory source files must be named C(*.oci.yml) or C(*.oci.yaml).

requirements:
  - "python >= 3.12"
  - "oci >= 2.90.0"
"""

EXAMPLES = r"""
# Minimal inventory source (stevefulme1.oci_cloud.yml):
plugin: stevefulme1.oci_cloud.oci_inventory
"""

import os
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

try:
    import oci
    from oci.identity import IdentityClient
    from oci.core import ComputeClient, VirtualNetworkClient
    from oci.database import DatabaseClient
    from oci.auth.signers import (
        InstancePrincipalsSecurityTokenSigner,
        get_resource_principals_signer,
    )

    HAS_OCI = True
except ImportError:
    HAS_OCI = False


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """OCI dynamic inventory plugin for Ansible."""

    NAME = "stevefulme1.oci_cloud.oci_inventory"

    def verify_file(self, path):
        """Accept only *.oci.yml / *.oci.yaml source files."""
        valid = False
        if super().verify_file(path):
            if path.endswith((".oci.yml", ".oci.yaml")):
                valid = True
        return valid

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------

    def _get_oci_config_and_signer(self):
        """Return (config_dict, signer_or_None) based on auth_type."""
        auth_type = self.get_option("auth_type")

        if auth_type == "instance_principal":
            signer = InstancePrincipalsSecurityTokenSigner()
            return {}, signer

        if auth_type == "resource_principal":
            signer = get_resource_principals_signer()
            return {}, signer

        # api_key (default)
        config_file = os.path.expanduser(self.get_option("config_file"))
        config_profile = self.get_option("config_profile")
        config = oci.config.from_file(
            file_location=config_file, profile_name=config_profile
        )
        oci.config.validate_config(config)
        return config, None

    def _create_client(self, client_class, region, config, signer):
        """Instantiate an OCI SDK client scoped to *region*."""
        kwargs = {}
        if signer is not None:
            kwargs["signer"] = signer
            kwargs["config"] = {"region": region}
        else:
            region_config = dict(config)
            region_config["region"] = region
            kwargs["config"] = region_config
        return client_class(**kwargs)

    # ------------------------------------------------------------------
    # Region / compartment discovery
    # ------------------------------------------------------------------

    def _get_regions(self, config, signer):
        """Return the list of regions to query."""
        regions = self.get_option("regions")
        if regions:
            return regions

        identity = (
            IdentityClient(config={}, signer=signer)
            if signer
            else IdentityClient(config)
        )
        tenancy_id = self._get_tenancy_id(config, signer)
        subscriptions = identity.list_region_subscriptions(tenancy_id).data
        return [s.region_name for s in subscriptions]

    def _get_tenancy_id(self, config, signer):
        """Determine the tenancy OCID."""
        if signer is not None:
            if hasattr(signer, "tenancy_id"):
                return signer.tenancy_id
            # For resource principals the tenancy can be derived from the
            # compartment of the calling resource — fall back to env var.
            tenancy = os.environ.get("OCI_TENANCY")
            if tenancy:
                return tenancy
            raise AnsibleError(
                "Unable to determine tenancy OCID. Set OCI_TENANCY env var "
                "when using resource_principal auth."
            )
        return config["tenancy"]

    def _get_compartments(self, config, signer):
        """Return the compartment OCIDs to search."""
        compartments = self.get_option("compartments")
        if compartments:
            return compartments
        return [self._get_tenancy_id(config, signer)]

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------

    def _get_vnic_attachments(self, compute_client, compartment_id, instance_id):
        """List VNIC attachments for a given instance."""
        return oci.pagination.list_call_get_all_results(
            compute_client.list_vnic_attachments,
            compartment_id,
            instance_id=instance_id,
        ).data

    def _get_primary_vnic_ips(self, vnet_client, vnic_attachments):
        """Return (public_ip, private_ip) from the primary VNIC."""
        for attachment in vnic_attachments:
            if attachment.lifecycle_state != "ATTACHED":
                continue
            try:
                vnic = vnet_client.get_vnic(attachment.vnic_id).data
                if vnic.is_primary:
                    return (
                        getattr(vnic, "public_ip", None),
                        getattr(vnic, "private_ip", None),
                    )
            except oci.exceptions.ServiceError:
                continue
        return None, None

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def _matches_filters(self, instance):
        """Return True when *instance* passes all configured tag filters."""
        filters = self.get_option("filters")
        if not filters:
            return True

        for namespace, tag_filters in filters.items():
            if namespace == "freeform":
                tags = instance.freeform_tags or {}
                for key, value in tag_filters.items():
                    if tags.get(key) != value:
                        return False
            else:
                defined = instance.defined_tags or {}
                ns_tags = defined.get(namespace, {})
                for key, value in tag_filters.items():
                    if ns_tags.get(key) != value:
                        return False
        return True

    # ------------------------------------------------------------------
    # Hostname resolution
    # ------------------------------------------------------------------

    def _resolve_hostname(self, preference, public_ip, private_ip, display_name):
        """Pick ansible_host based on hostname_preference order."""
        mapping = {
            "public_ip": public_ip,
            "private_ip": private_ip,
            "display_name": display_name,
        }
        for pref in preference:
            value = mapping.get(pref)
            if value:
                return value
        return display_name

    # ------------------------------------------------------------------
    # Auto-grouping helpers
    # ------------------------------------------------------------------

    def _sanitize_group(self, name):
        """Sanitize a string for use as an Ansible group name."""
        import re

        name = to_text(name)
        name = re.sub(r"[^A-Za-z0-9_]", "_", name)
        if name and name[0].isdigit():
            name = "_" + name
        return name

    def _add_host_to_groups(self, hostname, hostvars):
        """Create auto-groups and add *hostname* to them."""
        # Region
        region = hostvars.get("oci_region")
        if region:
            group = self._sanitize_group("region_" + region)
            self.inventory.add_group(group)
            self.inventory.add_host(hostname, group=group)

        # Compartment (last segment of OCID used as short id)
        compartment = hostvars.get("oci_compartment_id")
        if compartment:
            group = self._sanitize_group("compartment_" + compartment.split(".")[-1])
            self.inventory.add_group(group)
            self.inventory.add_host(hostname, group=group)

        # Availability domain
        ad = hostvars.get("oci_availability_domain")
        if ad:
            group = self._sanitize_group("ad_" + ad)
            self.inventory.add_group(group)
            self.inventory.add_host(hostname, group=group)

        # Shape
        shape = hostvars.get("oci_shape")
        if shape:
            group = self._sanitize_group("shape_" + shape)
            self.inventory.add_group(group)
            self.inventory.add_host(hostname, group=group)

        # Lifecycle state
        state = hostvars.get("oci_lifecycle_state")
        if state:
            group = self._sanitize_group("state_" + state.lower())
            self.inventory.add_group(group)
            self.inventory.add_host(hostname, group=group)

        # Freeform tags
        freeform_tags = hostvars.get("oci_freeform_tags") or {}
        for tag_key, tag_value in freeform_tags.items():
            group = self._sanitize_group("tag_" + tag_key + "_" + str(tag_value))
            self.inventory.add_group(group)
            self.inventory.add_host(hostname, group=group)

    # ------------------------------------------------------------------
    # Lifecycle state helpers
    # ------------------------------------------------------------------

    def _fetch_only_running_hosts(self):
        if self.get_option("fetch_only_running_hosts") is None:
            return True
        return self.get_option("fetch_only_running_hosts")

    # ------------------------------------------------------------------
    # Compute instance collection
    # ------------------------------------------------------------------

    def _fetch_compute_hosts(self, config, signer, regions, compartments):
        """Query compute instances and populate inventory."""
        hostname_preference = self.get_option("hostname_preference")

        for region in regions:
            compute = self._create_client(ComputeClient, region, config, signer)
            vnet = self._create_client(VirtualNetworkClient, region, config, signer)

            for compartment_id in compartments:
                try:
                    list_kwargs = dict()
                    if self._fetch_only_running_hosts():
                        list_kwargs["lifecycle_state"] = "RUNNING"
                    instances = oci.pagination.list_call_get_all_results(
                        compute.list_instances,
                        compartment_id,
                        **list_kwargs,
                    ).data
                except oci.exceptions.ServiceError as exc:
                    self.display.warning(
                        "Failed to list instances in compartment %s, region %s: %s"
                        % (compartment_id, region, to_native(exc))
                    )
                    continue

                for instance in instances:
                    if not self._matches_filters(instance):
                        continue

                    display_name = instance.display_name or instance.id

                    # Resolve IPs
                    try:
                        vnic_attachments = self._get_vnic_attachments(
                            compute, compartment_id, instance.id
                        )
                        public_ip, private_ip = self._get_primary_vnic_ips(
                            vnet, vnic_attachments
                        )
                    except oci.exceptions.ServiceError:
                        public_ip, private_ip = None, None

                    ansible_host = self._resolve_hostname(
                        hostname_preference, public_ip, private_ip, display_name
                    )

                    # Use display_name as the inventory hostname (sanitized)
                    hostname = self._sanitize_group(display_name)
                    self.inventory.add_host(hostname)

                    # Core host variables
                    hostvars = {
                        "ansible_host": ansible_host,
                        "oci_instance_id": instance.id,
                        "oci_compartment_id": instance.compartment_id,
                        "oci_availability_domain": instance.availability_domain,
                        "oci_shape": instance.shape,
                        "oci_region": region,
                        "oci_lifecycle_state": instance.lifecycle_state,
                        "oci_freeform_tags": instance.freeform_tags or {},
                        "oci_defined_tags": instance.defined_tags or {},
                        "oci_display_name": instance.display_name,
                        "oci_image_id": (
                            instance.source_details.image_id
                            if hasattr(instance, "source_details")
                            and instance.source_details
                            and hasattr(instance.source_details, "image_id")
                            else None
                        ),
                    }

                    if public_ip:
                        hostvars["oci_public_ip"] = public_ip
                    if private_ip:
                        hostvars["oci_private_ip"] = private_ip

                    for key, value in hostvars.items():
                        self.inventory.set_variable(hostname, key, value)

                    # Auto-groups
                    self._add_host_to_groups(hostname, hostvars)

                    # Constructable — keyed_groups, groups, compose
                    strict = self.get_option("strict")
                    self._set_composite_vars(
                        self.get_option("compose"), hostvars, hostname, strict=strict
                    )
                    self._add_host_to_composed_groups(
                        self.get_option("groups"), hostvars, hostname, strict=strict
                    )
                    self._add_host_to_keyed_groups(
                        self.get_option("keyed_groups"),
                        hostvars,
                        hostname,
                        strict=strict,
                    )

    # ------------------------------------------------------------------
    # DB system host collection
    # ------------------------------------------------------------------

    def _fetch_db_hosts(self, config, signer, regions, compartments):
        """Query Oracle DB system nodes and add them to inventory."""
        hostname_preference = self.get_option("hostname_preference")

        for region in regions:
            try:
                db_client = self._create_client(
                    DatabaseClient, region, config, signer
                )
                vnet = self._create_client(
                    VirtualNetworkClient, region, config, signer
                )
            except Exception:
                continue

            for compartment_id in compartments:
                try:
                    db_systems = oci.pagination.list_call_get_all_results(
                        db_client.list_db_systems, compartment_id
                    ).data
                except oci.exceptions.ServiceError as exc:
                    self.display.warning(
                        "Failed to list DB systems in compartment %s, region %s: %s"
                        % (compartment_id, region, to_native(exc))
                    )
                    continue

                for db_system in db_systems:
                    if db_system.lifecycle_state != "AVAILABLE":
                        continue

                    if not self._matches_filters(db_system):
                        continue

                    try:
                        db_nodes = oci.pagination.list_call_get_all_results(
                            db_client.list_db_nodes,
                            compartment_id,
                            db_system_id=db_system.id,
                        ).data
                    except oci.exceptions.ServiceError:
                        continue

                    for node in db_nodes:
                        if node.lifecycle_state != "AVAILABLE":
                            continue

                        display_name = (
                            db_system.display_name
                            + "_node_"
                            + (node.hostname or node.id.split(".")[-1])
                        )

                        # Resolve IPs from the VNIC
                        public_ip = None
                        private_ip = None
                        if node.vnic_id:
                            try:
                                vnic = vnet.get_vnic(node.vnic_id).data
                                public_ip = getattr(vnic, "public_ip", None)
                                private_ip = getattr(vnic, "private_ip", None)
                            except oci.exceptions.ServiceError:
                                pass

                        ansible_host = self._resolve_hostname(
                            hostname_preference, public_ip, private_ip, display_name
                        )

                        hostname = self._sanitize_group(display_name)
                        self.inventory.add_host(hostname)

                        hostvars = {
                            "ansible_host": ansible_host,
                            "oci_instance_id": node.id,
                            "oci_compartment_id": db_system.compartment_id,
                            "oci_availability_domain": db_system.availability_domain,
                            "oci_shape": db_system.shape,
                            "oci_region": region,
                            "oci_lifecycle_state": node.lifecycle_state,
                            "oci_freeform_tags": db_system.freeform_tags or {},
                            "oci_defined_tags": db_system.defined_tags or {},
                            "oci_display_name": display_name,
                            "oci_image_id": None,
                            "oci_db_system_id": db_system.id,
                        }

                        if public_ip:
                            hostvars["oci_public_ip"] = public_ip
                        if private_ip:
                            hostvars["oci_private_ip"] = private_ip

                        for key, value in hostvars.items():
                            self.inventory.set_variable(hostname, key, value)

                        self._add_host_to_groups(hostname, hostvars)

                        strict = self.get_option("strict")
                        self._set_composite_vars(
                            self.get_option("compose"),
                            hostvars,
                            hostname,
                            strict=strict,
                        )
                        self._add_host_to_composed_groups(
                            self.get_option("groups"),
                            hostvars,
                            hostname,
                            strict=strict,
                        )
                        self._add_host_to_keyed_groups(
                            self.get_option("keyed_groups"),
                            hostvars,
                            hostname,
                            strict=strict,
                        )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def parse(self, inventory, loader, path, cache=True):
        if not HAS_OCI:
            raise AnsibleError(
                "The OCI inventory plugin requires the 'oci' Python package. "
                "Install it with: pip install oci"
            )

        super().parse(inventory, loader, path, cache)
        self._read_config_data(path)

        cache_key = self.get_cache_key(path)
        use_cache = self.get_option("cache") and cache
        update_cache = False

        source_data = None
        if use_cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                update_cache = True

        if source_data:
            # Rebuild inventory from cached data
            self._populate_from_cache(source_data)
        else:
            # Live query
            config, signer = self._get_oci_config_and_signer()
            regions = self._get_regions(config, signer)
            compartments = self._get_compartments(config, signer)

            self._fetch_compute_hosts(config, signer, regions, compartments)

            if self.get_option("fetch_db_hosts"):
                self._fetch_db_hosts(config, signer, regions, compartments)

            if update_cache:
                self._cache[cache_key] = self._get_cache_data()

    # ------------------------------------------------------------------
    # Cache serialisation
    # ------------------------------------------------------------------

    def _get_cache_data(self):
        """Serialise current inventory state for caching."""
        cache_data = {}
        for host in self.inventory.hosts:
            host_obj = self.inventory.hosts[host]
            cache_data[host] = {
                "vars": dict(host_obj.vars),
                "groups": [g.name for g in host_obj.groups if g.name != "all"],
            }
        return cache_data

    def _populate_from_cache(self, cache_data):
        """Restore inventory from cached data."""
        for hostname, host_info in cache_data.items():
            self.inventory.add_host(hostname)
            for key, value in host_info.get("vars", {}).items():
                self.inventory.set_variable(hostname, key, value)
            for group_name in host_info.get("groups", []):
                self.inventory.add_group(group_name)
                self.inventory.add_host(hostname, group=group_name)

            hostvars = host_info.get("vars", {})
            strict = self.get_option("strict")
            self._set_composite_vars(
                self.get_option("compose"), hostvars, hostname, strict=strict
            )
            self._add_host_to_composed_groups(
                self.get_option("groups"), hostvars, hostname, strict=strict
            )
            self._add_host_to_keyed_groups(
                self.get_option("keyed_groups"), hostvars, hostname, strict=strict
            )
