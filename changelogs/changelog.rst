==============================
oracle.oci Release Notes
==============================

.. contents:: Topics

v1.1.0
======

Release Summary
---------------

Added 102 new modules for feature parity with AWS, Azure, and GCP Ansible
collections. The collection now contains 158 modules covering 11 OCI service
categories. Tracked under ANSTRAT-1978.

New Modules
-----------

Compute
~~~~~~~

- oci_autoscaling_configuration - Manage autoscaling configurations
- oci_capacity_reservation - Manage compute capacity reservations
- oci_cluster_network - Manage cluster networks
- oci_instance_console_history - Manage instance console history
- oci_vnic_attachment - Manage VNIC attachments
- oci_volume_attachment - Manage volume attachments
- oci_volume_group - Manage volume groups
- oci_volume_backup_policy - Manage volume backup policies

Networking
~~~~~~~~~~

- oci_network_load_balancer - Manage Network Load Balancers
- oci_ipsec_connection - Manage IPSec VPN connections
- oci_local_peering_gateway - Manage local peering gateways
- oci_remote_peering_connection - Manage remote peering connections
- oci_dhcp_options - Manage DHCP options
- oci_private_endpoint - Manage private endpoints
- oci_public_ip - Manage reserved public IPs
- oci_private_ip - Manage secondary private IPs
- oci_network_firewall - Manage OCI Network Firewalls
- oci_network_firewall_policy - Manage Network Firewall policies
- oci_vtap - Manage virtual test access points (VTAPs)
- oci_capture_filter - Manage VTAP capture filters
- oci_nsg_rule - Manage Network Security Group rules
- oci_traffic_management_steering_policy - Manage DNS traffic management steering policies
- oci_fastconnect - Manage FastConnect virtual circuits
- oci_cross_connect - Manage cross-connect resources

Database
~~~~~~~~

- oci_mysql_db_system - Manage MySQL Database Service systems
- oci_nosql_table - Manage NoSQL Database tables
- oci_postgresql_db_system - Manage PostgreSQL Database systems
- oci_exadata_infrastructure - Manage Exadata Cloud Infrastructure
- oci_vm_cluster - Manage Exadata VM clusters
- oci_db_home - Manage Database Homes
- oci_pluggable_database - Manage Pluggable Databases
- oci_external_database - Manage external database connectors
- oci_database_migration - Manage Database Migration Service migrations
- oci_goldengate_deployment - Manage GoldenGate deployments
- oci_goldengate_connection - Manage GoldenGate connections

Security and IAM
~~~~~~~~~~~~~~~~

- oci_waf - Manage Web Application Firewalls
- oci_bastion - Manage Bastion Service instances
- oci_certificate - Manage OCI Certificates
- oci_identity_domain - Manage Identity Domains
- oci_auth_token - Manage user auth tokens
- oci_customer_secret_key - Manage S3-compatible secret keys
- oci_smtp_credential - Manage SMTP credentials
- oci_network_source - Manage network source restrictions
- oci_tag_default - Manage tag defaults
- oci_quota - Manage compartment quotas
- oci_security_zone - Manage Security Zones
- oci_cloud_guard_detector_recipe - Manage Cloud Guard detector recipes
- oci_cloud_guard_responder_recipe - Manage Cloud Guard responder recipes
- oci_vulnerability_scan - Manage Vulnerability Scanning host scan recipes

Storage
~~~~~~~

- oci_preauthenticated_request - Manage Object Storage pre-authenticated requests
- oci_object_lifecycle_policy - Manage Object Storage lifecycle policies
- oci_replication_policy - Manage Object Storage cross-region replication
- oci_retention_rule - Manage Object Storage retention rules
- oci_export_set - Manage File Storage export sets
- oci_snapshot - Manage File Storage snapshots

Observability
~~~~~~~~~~~~~

- oci_log - Manage Logging service log resources
- oci_log_analytics_entity - Manage Log Analytics entities
- oci_health_check - Manage HTTP health check monitors
- oci_apm_domain - Manage APM domains
- oci_service_connector - Manage Service Connector Hub connectors
- oci_management_agent - Manage Management Agents
- oci_os_management - Manage OS Management instances
- oci_alarm_suppression - Manage alarm suppression windows
- oci_notification_subscription - Manage notification subscriptions

DevOps
~~~~~~

- oci_devops_project - Manage DevOps projects
- oci_devops_repository - Manage DevOps code repositories
- oci_devops_build_pipeline - Manage DevOps build pipelines
- oci_devops_deploy_pipeline - Manage DevOps deployment pipelines
- oci_artifact_repository - Manage Artifact Registry repositories
- oci_container_registry - Manage Container Registry repositories

Serverless and Application Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- oci_functions_application - Manage Functions applications
- oci_functions_function - Manage Functions functions
- oci_api_gateway - Manage API Gateways
- oci_api_gateway_deployment - Manage API Gateway deployments
- oci_streaming - Manage Streaming streams
- oci_queue - Manage Queue service queues
- oci_email_delivery - Manage Email Delivery senders
- oci_integration_instance - Manage Integration instances
- oci_visual_builder - Manage Visual Builder instances
- oci_digital_assistant - Manage Digital Assistant instances

AI and Machine Learning
~~~~~~~~~~~~~~~~~~~~~~~

- oci_data_science_project - Manage Data Science projects
- oci_data_science_notebook - Manage Data Science notebook sessions
- oci_data_science_model - Manage Data Science models
- oci_data_science_model_deployment - Manage Data Science model deployments
- oci_ai_vision_project - Manage AI Vision projects
- oci_ai_language_project - Manage AI Language projects
- oci_ai_speech_transcription - Manage AI Speech transcription jobs
- oci_ai_anomaly_detection - Manage AI Anomaly Detection projects
- oci_generative_ai_model - Manage Generative AI models
- oci_generative_ai_endpoint - Manage Generative AI endpoints

Data and Analytics
~~~~~~~~~~~~~~~~~~

- oci_data_integration_workspace - Manage Data Integration workspaces
- oci_data_catalog - Manage Data Catalog instances
- oci_data_flow_application - Manage Data Flow applications
- oci_data_safe - Manage Data Safe configurations
- oci_data_labeling_dataset - Manage Data Labeling datasets
- oci_analytics_instance - Manage Analytics Cloud instances
- oci_big_data_service - Manage Big Data Service clusters
- oci_opensearch_cluster - Manage OpenSearch clusters

Migration and Governance
~~~~~~~~~~~~~~~~~~~~~~~~

- oci_budget - Manage budgets
- oci_resource_manager_stack - Manage Resource Manager stacks
- oci_cloud_migration - Manage Cloud Migrations
- oci_ocb_inventory - Manage Oracle Cloud Bridge inventories

Bugfixes
--------

- oci_big_data_service - Removed invalid ``no_log`` from DOCUMENTATION block.
- oci_service_connector - Added missing ``elements: dict`` to ``log_sources`` list parameter.

v1.0.0
======

Release Summary
---------------

Initial release of the ``oracle.oci`` Ansible collection with 56 modules
and a dynamic inventory plugin for Oracle Cloud Infrastructure.

New Modules
-----------

Compute
~~~~~~~

- oci_instance - Manage compute instances (create, update, terminate)
- oci_instance_pool - Manage instance pools
- oci_image - Manage custom images
- oci_boot_volume - Manage boot volumes

Networking
~~~~~~~~~~

- oci_vcn - Manage Virtual Cloud Networks
- oci_subnet - Manage subnets
- oci_internet_gateway - Manage internet gateways
- oci_nat_gateway - Manage NAT gateways
- oci_service_gateway - Manage service gateways
- oci_drg - Manage Dynamic Routing Gateways
- oci_route_table - Manage route tables
- oci_security_list - Manage security lists
- oci_nsg - Manage Network Security Groups
- oci_load_balancer - Manage load balancers

Database
~~~~~~~~

- oci_autonomous_database - Manage Autonomous Databases (ATP/ADW)
- oci_db_system - Manage DB Systems
- oci_db_backup - Manage database backups
- oci_data_guard - Manage Data Guard associations

Identity and Access Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- oci_compartment - Manage compartments
- oci_user - Manage users
- oci_group - Manage groups
- oci_policy - Manage IAM policies
- oci_dynamic_group - Manage dynamic groups
- oci_api_key - Manage user API keys
- oci_tag_namespace - Manage tag namespaces
- oci_tag - Manage tags

Storage
~~~~~~~

- oci_bucket - Manage Object Storage buckets
- oci_object - Manage objects in Object Storage
- oci_volume - Manage block volumes
- oci_volume_backup - Manage block volume backups
- oci_file_system - Manage File Storage file systems
- oci_mount_target - Manage File Storage mount targets
- oci_export - Manage File Storage exports

Container and Kubernetes
~~~~~~~~~~~~~~~~~~~~~~~~

- oci_oke_cluster - Manage OKE Kubernetes clusters
- oci_oke_node_pool - Manage OKE node pools
- oci_container_instance - Manage Container Instances

Security
~~~~~~~~

- oci_vault - Manage vaults and secrets
- oci_key - Manage encryption keys
- oci_cloud_guard - Manage Cloud Guard targets

Observability
~~~~~~~~~~~~~

- oci_alarm - Manage monitoring alarms
- oci_log_group - Manage log groups
- oci_events_rule - Manage Events rules
- oci_notification_topic - Manage notification topics

DNS
~~~

- oci_dns_zone - Manage DNS zones

New Plugins
-----------

Inventory
~~~~~~~~~

- oci_inventory - Dynamic inventory plugin for OCI compute instances
