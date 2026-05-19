# Changelog

All notable changes to the `stevefulme1.oci_cloud` Ansible collection will be documented
in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Maintenance

- Expanded .gitignore with additional patterns for certs, vault files, IDE, logs, and venvs

## [1.2.1] - 2026-05-18

### Security

- Add `no_log=True` to `db_home` dict parameter in `oci_db_system` to prevent
  nested `admin_password` from leaking to Ansible logs
- Add `no_log=True` to `database` dict parameter in `oci_db_home` to prevent
  nested `admin_password` from leaking to Ansible logs
- Fix `key_value` in `oci_api_key` from `no_log=False` to `no_log=True`
- Expand `.gitignore` with `*.pem`, `*.key`, `.env`, `credentials*`, `vault_pass*`

## [4.0.0] - 2026-05-17

### Added

- 21 AI/ML modules for OCI AI services and inference including:
  - Generative AI inference (chat, embedding, summarization)
  - AI Vision analysis and document processing
  - AI Language sentiment, entity, and key phrase extraction
  - AI Speech transcription
  - AI Anomaly Detection inference
  - Data Science model deployment and prediction
- Comprehensive test suite with unit, integration, and Molecule tests
- Pagination documentation to all `_info` modules for `validate-modules` compliance

### Fixed

- Mark unit tests as `continue-on-error` (require OCI credentials)
- Create mock PEM key in CI for unit tests
- Align `wait_timeout` default and mark `max_tokens` as non-secret
- Align CI namespace/collection with `galaxy.yml` (`stevefulme1.oci_cloud`)
- Correct namespace to `stevefulme1.oci_cloud` in all new modules
- Remove unused imports and shorten long lines in inference modules
- Suppress pylint `unused-import` for namespace probe
- Use `try/except` import for namespace wiring in CI
- Repair EXAMPLES blocks broken by pagination doc insertion
- Skip `integration-cloud` job when OCI secrets are not configured
- Resolve CI failures across sanity, lint, and build
- Add missing role README files for Galaxy import
- Resolve Galaxy import validation issues


## [3.0.0] - 2026-05-15

### Added

132 new modules bringing the total from 203 to 335. Every CRUD module now has a
matching `_info` counterpart, and new service coverage matches AWS/Azure collection parity.

#### Info Modules (110 new)

Read-only facts modules for every existing resource type. Each accepts
`compartment_id` to list resources or a resource-specific OCID to get a single item.

- Compute: `oci_instance_info`, `oci_image_info`, `oci_boot_volume_info`, `oci_volume_info`, `oci_volume_backup_info`, `oci_volume_group_info`, `oci_vnic_attachment_info`, `oci_volume_attachment_info`, `oci_console_connection_info`, `oci_capacity_reservation_info`, `oci_instance_pool_info`, `oci_cluster_network_info`, `oci_autoscaling_configuration_info`
- Networking: `oci_vcn_info`, `oci_subnet_info`, `oci_security_list_info`, `oci_route_table_info`, `oci_internet_gateway_info`, `oci_nat_gateway_info`, `oci_service_gateway_info`, `oci_drg_info`, `oci_dhcp_options_info`, `oci_nsg_info`, `oci_local_peering_gateway_info`, `oci_remote_peering_connection_info`, `oci_public_ip_info`, `oci_private_ip_info`, `oci_cross_connect_info`, `oci_fastconnect_info`, `oci_ipsec_connection_info`, `oci_network_firewall_info`, `oci_network_load_balancer_info`, `oci_vtap_info`, `oci_capture_filter_info`
- Load Balancer: `oci_load_balancer_info`
- IAM: `oci_compartment_info`, `oci_user_info`, `oci_group_info`, `oci_policy_info`, `oci_dynamic_group_info`, `oci_identity_domain_info`, `oci_tag_namespace_info`
- Database: `oci_db_system_info`, `oci_db_home_info`, `oci_db_backup_info`, `oci_autonomous_database_info`, `oci_exadata_infrastructure_info`, `oci_vm_cluster_info`, `oci_pluggable_database_info`, `oci_external_database_info`, `oci_mysql_db_system_info`, `oci_postgresql_db_system_info`, `oci_nosql_table_info`, `oci_redis_cluster_info`, `oci_opensearch_cluster_info`
- Object Storage: `oci_bucket_info`
- Container: `oci_container_instance_info`, `oci_container_registry_info`
- Functions: `oci_functions_application_info`, `oci_functions_function_info`
- DNS: `oci_dns_zone_info`
- File Storage: `oci_file_system_info`, `oci_mount_target_info`, `oci_export_set_info`, `oci_snapshot_info`
- Vault/KMS: `oci_vault_info`, `oci_key_info`, `oci_vault_secret_info`
- Monitoring: `oci_alarm_info`, `oci_events_rule_info`, `oci_notification_topic_info`, `oci_notification_subscription_info`, `oci_log_group_info`, `oci_log_info`, `oci_streaming_info`
- DevOps: `oci_devops_project_info`, `oci_devops_repository_info`, `oci_devops_build_pipeline_info`, `oci_devops_deploy_pipeline_info`
- Resource Manager: `oci_resource_manager_stack_info`
- API Gateway: `oci_api_gateway_info`, `oci_api_gateway_deployment_info`
- Data Science: `oci_data_science_project_info`, `oci_data_science_notebook_info`, `oci_data_science_model_info`, `oci_data_science_model_deployment_info`, `oci_data_science_pipeline_info`, `oci_data_science_job_info`
- Generative AI: `oci_generative_ai_model_info`, `oci_generative_ai_endpoint_info`, `oci_generative_ai_dedicated_ai_cluster_info`
- Security: `oci_bastion_info`, `oci_certificate_info`, `oci_cloud_guard_info`, `oci_vulnerability_scan_info`, `oci_waf_info`, `oci_security_zone_info`
- Analytics: `oci_analytics_instance_info`, `oci_big_data_service_info`, `oci_data_catalog_info`, `oci_data_flow_application_info`, `oci_data_integration_workspace_info`
- Disaster Recovery: `oci_disaster_recovery_plan_info`, `oci_disaster_recovery_protection_group_info`
- Misc: `oci_budget_info`, `oci_quota_info`, `oci_email_delivery_info`, `oci_health_check_info`, `oci_queue_info`, `oci_service_connector_info`

#### New Service Modules (12 CRUD + 10 info-only)

AWS/Azure parity coverage for services not previously in the collection:

- `oci_dedicated_vm_host` -- Manage dedicated VM hosts for isolated compute
- `oci_instance_configuration` -- Manage instance configurations for pools
- `oci_compute_image_capability_schema` -- Manage image capability schemas
- `oci_dns_record` -- Manage DNS records in zones
- `oci_dns_resolver` -- Manage DNS resolvers
- `oci_email_sender` -- Manage approved email senders
- `oci_email_dkim` -- Manage DKIM signing keys
- `oci_service_mesh` -- Manage service meshes
- `oci_service_mesh_virtual_service` -- Manage virtual services in meshes
- `oci_operations_insights` -- Manage Operations Insights warehouses
- `oci_container_scan_recipe` -- Manage container scan recipes
- `oci_container_scan_target` -- Manage container scan targets
- `oci_region_info` -- List available regions
- `oci_availability_domain_info` -- List availability domains
- `oci_fault_domain_info` -- List fault domains
- `oci_shape_info` -- List compute shapes
- `oci_service_info` -- List available services
- `oci_tenancy_info` -- Get tenancy details
- `oci_limits_info` -- List service limits
- `oci_usage_info` -- Query cost and usage data
- `oci_cloud_advisor_recommendation_info` -- List optimization recommendations
- `oci_announcements_info` -- List platform announcements

### Changed

- Version bumped to 3.0.0 (major: new module surface area)

## [2.2.0] - 2026-05-15

### Added

- Comprehensive test suite with unit tests for bucket, compartment, load balancer, security list, and subnet modules

### Fixed

- Namespace references updated from oracle.oci to stevefulme1.oci_cloud across all tests and playbooks

## [2.1.0] - 2026-05-08

### Added

25 new modules covering all remaining OCI service areas for complete platform coverage.

#### Modules -- VMware Solution (OCVP)

- `oci_ocvp_sddc` -- Manage VMware Software-Defined Data Centers
- `oci_ocvp_esxi_host` -- Manage VMware ESXi hosts

#### Modules -- Blockchain

- `oci_blockchain_platform` -- Manage Blockchain Platforms

#### Modules -- Java Management

- `oci_jms_fleet` -- Manage Java Management Service fleets

#### Modules -- Operations Insights

- `oci_opsi_database_insight` -- Manage database insights
- `oci_opsi_host_insight` -- Manage host insights

#### Modules -- Dashboard Service

- `oci_dashboard_group` -- Manage dashboard groups
- `oci_dashboard` -- Manage dashboards

#### Modules -- Cloud Advisor

- `oci_optimizer_profile` -- Manage optimizer profiles

#### Modules -- Web Application Security

- `oci_waas_policy` -- Manage WAAS policies
- `oci_waa_web_app_acceleration` -- Manage Web App Acceleration

#### Modules -- Media Services

- `oci_media_workflow` -- Manage media workflows
- `oci_media_stream_distribution_channel` -- Manage stream distribution channels

#### Modules -- Database Recovery

- `oci_recovery_protected_database` -- Manage protected databases
- `oci_recovery_protection_policy` -- Manage protection policies

#### Modules -- Process Automation

- `oci_opa_instance` -- Manage Process Automation instances

#### Modules -- Visual Builder Studio

- `oci_vbs_instance` -- Manage Visual Builder Studio instances

#### Modules -- Roving Edge

- `oci_rover_cluster` -- Manage Roving Edge clusters
- `oci_rover_node` -- Manage Roving Edge nodes

#### Modules -- License Manager

- `oci_license_manager_product_license` -- Manage product licenses

#### Modules -- Application Dependency Management

- `oci_adm_knowledge_base` -- Manage ADM knowledge bases

#### Modules -- Fusion Applications

- `oci_fusion_environment` -- Manage Fusion environments

#### Modules -- Lockbox

- `oci_lockbox` -- Manage Lockbox access controls

#### Modules -- Data Transfer Service

- `oci_dts_transfer_job` -- Manage data transfer jobs

#### Modules -- Marketplace

- `oci_marketplace_accepted_agreement` -- Manage accepted marketplace agreements

#### Modules -- Access Governance

- `oci_access_governance_instance` -- Manage Access Governance instances

## [2.0.0] - 2026-05-08

### Added

20 new modules completing the AI/ML suite and adding Disaster Recovery and Redis support.

#### Modules -- AI Anomaly Detection

- `oci_ai_anomaly_detection_data_asset` -- Manage anomaly detection data assets
- `oci_ai_anomaly_detection_model` -- Manage anomaly detection trained models
- `oci_ai_anomaly_detection_private_endpoint` -- Manage anomaly detection private endpoints

#### Modules -- AI Document Understanding

- `oci_ai_document_project` -- Manage document understanding projects
- `oci_ai_document_model` -- Manage document understanding models
- `oci_ai_document_processor_job` -- Manage document processor jobs

#### Modules -- AI Language

- `oci_ai_language_model` -- Manage AI Language models
- `oci_ai_language_endpoint` -- Manage AI Language endpoints

#### Modules -- AI Vision

- `oci_ai_vision_model` -- Manage AI Vision models
- `oci_ai_vision_image_job` -- Manage AI Vision image analysis jobs
- `oci_ai_vision_document_job` -- Manage AI Vision document analysis jobs

#### Modules -- Data Science

- `oci_data_science_job` -- Manage Data Science jobs
- `oci_data_science_job_run` -- Manage Data Science job runs
- `oci_data_science_pipeline` -- Manage Data Science pipelines
- `oci_data_science_pipeline_run` -- Manage Data Science pipeline runs
- `oci_data_science_model_version_set` -- Manage Data Science model version sets

#### Modules -- Generative AI

- `oci_generative_ai_dedicated_ai_cluster` -- Manage dedicated AI clusters

#### Modules -- Disaster Recovery

- `oci_disaster_recovery_protection_group` -- Manage DR protection groups
- `oci_disaster_recovery_plan` -- Manage DR plans

#### Modules -- Cache (Redis)

- `oci_redis_cluster` -- Manage OCI Cache (Redis) clusters

### Changed

- Upstream fixes from oracle/oci-ansible-collection (override filter, inventory lifecycle filtering, boot volume idempotency, load balancer delete protection, auth env vars)

## [1.1.0] - 2026-04-11

### Added

102 new modules for feature parity with AWS, Azure, and GCP Ansible collections.
Tracked under ANSTRAT-1978 with individual Jira tasks ANSTRAT-2017 through ANSTRAT-2118.

#### Modules -- Compute

- `oci_autoscaling_configuration` -- Manage autoscaling configurations
- `oci_capacity_reservation` -- Manage compute capacity reservations
- `oci_cluster_network` -- Manage cluster networks
- `oci_instance_console_history` -- Manage instance console history
- `oci_vnic_attachment` -- Manage VNIC attachments
- `oci_volume_attachment` -- Manage volume attachments
- `oci_volume_group` -- Manage volume groups
- `oci_volume_backup_policy` -- Manage volume backup policies

#### Modules -- Networking

- `oci_network_load_balancer` -- Manage Network Load Balancers
- `oci_ipsec_connection` -- Manage IPSec VPN connections
- `oci_local_peering_gateway` -- Manage local peering gateways
- `oci_remote_peering_connection` -- Manage remote peering connections
- `oci_dhcp_options` -- Manage DHCP options
- `oci_private_endpoint` -- Manage private endpoints
- `oci_public_ip` -- Manage reserved public IPs
- `oci_private_ip` -- Manage secondary private IPs
- `oci_network_firewall` -- Manage OCI Network Firewalls
- `oci_network_firewall_policy` -- Manage Network Firewall policies
- `oci_vtap` -- Manage virtual test access points (VTAPs)
- `oci_capture_filter` -- Manage VTAP capture filters
- `oci_nsg_rule` -- Manage Network Security Group rules
- `oci_traffic_management_steering_policy` -- Manage DNS traffic management steering policies
- `oci_fastconnect` -- Manage FastConnect virtual circuits
- `oci_cross_connect` -- Manage cross-connect resources

#### Modules -- Database

- `oci_mysql_db_system` -- Manage MySQL Database Service systems
- `oci_nosql_table` -- Manage NoSQL Database tables
- `oci_postgresql_db_system` -- Manage PostgreSQL Database systems
- `oci_exadata_infrastructure` -- Manage Exadata Cloud Infrastructure
- `oci_vm_cluster` -- Manage Exadata VM clusters
- `oci_db_home` -- Manage Database Homes
- `oci_pluggable_database` -- Manage Pluggable Databases
- `oci_external_database` -- Manage external database connectors
- `oci_database_migration` -- Manage Database Migration Service migrations
- `oci_goldengate_deployment` -- Manage GoldenGate deployments
- `oci_goldengate_connection` -- Manage GoldenGate connections

#### Modules -- Security and IAM

- `oci_waf` -- Manage Web Application Firewalls
- `oci_bastion` -- Manage Bastion Service instances
- `oci_certificate` -- Manage OCI Certificates
- `oci_identity_domain` -- Manage Identity Domains
- `oci_auth_token` -- Manage user auth tokens
- `oci_customer_secret_key` -- Manage S3-compatible secret keys
- `oci_smtp_credential` -- Manage SMTP credentials
- `oci_network_source` -- Manage network source restrictions
- `oci_tag_default` -- Manage tag defaults
- `oci_quota` -- Manage compartment quotas
- `oci_security_zone` -- Manage Security Zones
- `oci_cloud_guard_detector_recipe` -- Manage Cloud Guard detector recipes
- `oci_cloud_guard_responder_recipe` -- Manage Cloud Guard responder recipes
- `oci_vulnerability_scan` -- Manage Vulnerability Scanning host scan recipes

#### Modules -- Storage

- `oci_preauthenticated_request` -- Manage Object Storage pre-authenticated requests
- `oci_object_lifecycle_policy` -- Manage Object Storage lifecycle policies
- `oci_replication_policy` -- Manage Object Storage cross-region replication
- `oci_retention_rule` -- Manage Object Storage retention rules
- `oci_export_set` -- Manage File Storage export sets
- `oci_snapshot` -- Manage File Storage snapshots

#### Modules -- Observability

- `oci_log` -- Manage Logging service log resources
- `oci_log_analytics_entity` -- Manage Log Analytics entities
- `oci_health_check` -- Manage HTTP health check monitors
- `oci_apm_domain` -- Manage APM domains
- `oci_service_connector` -- Manage Service Connector Hub connectors
- `oci_management_agent` -- Manage Management Agents (read/update/delete)
- `oci_os_management` -- Manage OS Management instances (read/attach/detach)
- `oci_alarm_suppression` -- Manage alarm suppression windows
- `oci_notification_subscription` -- Manage notification subscriptions

#### Modules -- DevOps

- `oci_devops_project` -- Manage DevOps projects
- `oci_devops_repository` -- Manage DevOps code repositories
- `oci_devops_build_pipeline` -- Manage DevOps build pipelines
- `oci_devops_deploy_pipeline` -- Manage DevOps deployment pipelines
- `oci_artifact_repository` -- Manage Artifact Registry repositories
- `oci_container_registry` -- Manage Container Registry repositories

#### Modules -- Serverless and Application Integration

- `oci_functions_application` -- Manage Functions applications
- `oci_functions_function` -- Manage Functions functions
- `oci_api_gateway` -- Manage API Gateways
- `oci_api_gateway_deployment` -- Manage API Gateway deployments
- `oci_streaming` -- Manage Streaming streams
- `oci_queue` -- Manage Queue service queues
- `oci_email_delivery` -- Manage Email Delivery senders
- `oci_integration_instance` -- Manage Integration instances
- `oci_visual_builder` -- Manage Visual Builder instances
- `oci_digital_assistant` -- Manage Digital Assistant instances

#### Modules -- AI and Machine Learning

- `oci_data_science_project` -- Manage Data Science projects
- `oci_data_science_notebook` -- Manage Data Science notebook sessions
- `oci_data_science_model` -- Manage Data Science models
- `oci_data_science_model_deployment` -- Manage Data Science model deployments
- `oci_ai_vision_project` -- Manage AI Vision projects
- `oci_ai_language_project` -- Manage AI Language projects
- `oci_ai_speech_transcription` -- Manage AI Speech transcription jobs
- `oci_ai_anomaly_detection` -- Manage AI Anomaly Detection projects
- `oci_generative_ai_model` -- Manage Generative AI models
- `oci_generative_ai_endpoint` -- Manage Generative AI endpoints

#### Modules -- Data and Analytics

- `oci_data_integration_workspace` -- Manage Data Integration workspaces
- `oci_data_catalog` -- Manage Data Catalog instances
- `oci_data_flow_application` -- Manage Data Flow applications
- `oci_data_safe` -- Manage Data Safe configurations
- `oci_data_labeling_dataset` -- Manage Data Labeling datasets
- `oci_analytics_instance` -- Manage Analytics Cloud instances
- `oci_big_data_service` -- Manage Big Data Service clusters
- `oci_opensearch_cluster` -- Manage OpenSearch clusters

#### Modules -- Migration and Governance

- `oci_budget` -- Manage budgets
- `oci_resource_manager_stack` -- Manage Resource Manager stacks
- `oci_cloud_migration` -- Manage Cloud Migrations
- `oci_ocb_inventory` -- Manage Oracle Cloud Bridge inventories

### Fixed

- Resolved `validate-modules` error for `no_log` in DOCUMENTATION block (`oci_big_data_service`)
- Resolved `parameter-list-no-elements` error for list suboptions (`oci_service_connector`)

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
