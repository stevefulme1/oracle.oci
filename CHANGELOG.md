# Changelog

All notable changes to the `oracle.oci` Ansible collection will be documented
in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-10

### Added

#### Modules -- Compute
- `oci_instance` -- Manage compute instances (create, update, terminate)
- `oci_instance_pool` -- Manage instance pools
- `oci_image` -- Manage custom images
- `oci_boot_volume` -- Manage boot volumes

#### Modules -- Networking
- `oci_vcn` -- Manage Virtual Cloud Networks
- `oci_subnet` -- Manage subnets
- `oci_internet_gateway` -- Manage internet gateways
- `oci_nat_gateway` -- Manage NAT gateways
- `oci_service_gateway` -- Manage service gateways
- `oci_drg` -- Manage Dynamic Routing Gateways
- `oci_route_table` -- Manage route tables
- `oci_security_list` -- Manage security lists
- `oci_nsg` -- Manage Network Security Groups
- `oci_load_balancer` -- Manage load balancers

#### Modules -- Database
- `oci_autonomous_database` -- Manage Autonomous Databases (ATP/ADW)
- `oci_db_system` -- Manage DB Systems
- `oci_db_backup` -- Manage database backups
- `oci_data_guard` -- Manage Data Guard associations

#### Modules -- Identity and Access Management
- `oci_compartment` -- Manage compartments
- `oci_user` -- Manage users
- `oci_group` -- Manage groups
- `oci_policy` -- Manage IAM policies
- `oci_dynamic_group` -- Manage dynamic groups
- `oci_api_key` -- Manage user API keys
- `oci_tag_namespace` -- Manage tag namespaces
- `oci_tag` -- Manage tags

#### Modules -- Storage
- `oci_bucket` -- Manage Object Storage buckets
- `oci_object` -- Manage objects in Object Storage
- `oci_volume` -- Manage block volumes
- `oci_volume_backup` -- Manage block volume backups
- `oci_file_system` -- Manage File Storage file systems
- `oci_mount_target` -- Manage File Storage mount targets
- `oci_export` -- Manage File Storage exports

#### Modules -- Container and Kubernetes
- `oci_oke_cluster` -- Manage OKE Kubernetes clusters
- `oci_oke_node_pool` -- Manage OKE node pools
- `oci_container_instance` -- Manage Container Instances

#### Modules -- Security
- `oci_vault` -- Manage vaults and secrets
- `oci_key` -- Manage encryption keys
- `oci_cloud_guard` -- Manage Cloud Guard targets

#### Modules -- Observability
- `oci_alarm` -- Manage monitoring alarms
- `oci_log_group` -- Manage log groups
- `oci_events_rule` -- Manage Events rules
- `oci_notification_topic` -- Manage notification topics

#### Modules -- DNS
- `oci_dns_zone` -- Manage DNS zones

#### Inventory Plugin
- `oci_inventory` -- Dynamic inventory plugin for OCI compute instances

#### Module Utilities
- `oci_auth` -- Authentication helper (API key, instance principal, resource principal, session token)
- `oci_common` -- Common parameters and validation
- `oci_resource` -- Base resource management class
- `oci_wait` -- Waiter utilities for lifecycle state transitions
