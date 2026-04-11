# Oracle Cloud Infrastructure (OCI) Ansible Collection

[![CI](https://github.com/stevefulme1/oracle.oci/actions/workflows/ci.yml/badge.svg)](https://github.com/stevefulme1/oracle.oci/actions/workflows/ci.yml)

Ansible Collection for managing Oracle Cloud Infrastructure resources.
Provides 158 modules covering compute, networking, database, IAM, storage,
security, observability, DevOps, serverless, AI/ML, data analytics, and a
dynamic inventory plugin.

## Requirements

| Dependency | Version |
|---|---|
| Python | >= 3.12 |
| ansible-core | >= 2.16.0 |
| OCI Python SDK (`oci`) | >= 2.90.0 |

## Installation

```bash
ansible-galaxy collection install oracle.oci
```

Install the Python dependency:

```bash
pip install oci>=2.90.0
```

## Authentication

Configure OCI credentials using one of the following methods:

1. **Config file** (default): `~/.oci/config`
2. **Environment variables**: `OCI_USER_ID`, `OCI_TENANCY_ID`, `OCI_REGION`, `OCI_FINGERPRINT`, `OCI_KEY_FILE`
3. **Instance principal**: Set `auth_type: instance_principal`
4. **Resource principal**: Set `auth_type: resource_principal`
5. **Session token**: Set `auth_type: session_token`

All modules accept the common authentication parameters defined in the
`oracle.oci.oci_common` documentation fragment.

## Modules

### Compute

| Module | Description |
|---|---|
| `oci_instance` | Manage compute instances |
| `oci_instance_pool` | Manage instance pools |
| `oci_instance_facts` | Gather compute instance facts |
| `oci_instance_console_history` | Manage instance console history |
| `oci_image` | Manage custom images |
| `oci_boot_volume` | Manage boot volumes |
| `oci_autoscaling_configuration` | Manage autoscaling configurations |
| `oci_capacity_reservation` | Manage compute capacity reservations |
| `oci_cluster_network` | Manage cluster networks |
| `oci_console_connection` | Manage instance console connections |
| `oci_vnic_attachment` | Manage VNIC attachments |
| `oci_volume_attachment` | Manage volume attachments |
| `oci_volume_group` | Manage volume groups |
| `oci_volume_backup_policy` | Manage volume backup policies |

### Networking

| Module | Description |
|---|---|
| `oci_vcn` | Manage Virtual Cloud Networks |
| `oci_subnet` | Manage subnets |
| `oci_route_table` | Manage route tables |
| `oci_security_list` | Manage security lists |
| `oci_nsg` | Manage Network Security Groups |
| `oci_nsg_rule` | Manage NSG rules |
| `oci_internet_gateway` | Manage internet gateways |
| `oci_nat_gateway` | Manage NAT gateways |
| `oci_service_gateway` | Manage service gateways |
| `oci_drg` | Manage Dynamic Routing Gateways |
| `oci_dhcp_options` | Manage DHCP options |
| `oci_load_balancer` | Manage load balancers |
| `oci_load_balancer_backend` | Manage load balancer backends |
| `oci_load_balancer_backend_set` | Manage load balancer backend sets |
| `oci_load_balancer_health_checker` | Manage load balancer health checkers |
| `oci_load_balancer_listener` | Manage load balancer listeners |
| `oci_network_load_balancer` | Manage Network Load Balancers |
| `oci_dns_zone` | Manage DNS zones |
| `oci_ipsec_connection` | Manage IPSec VPN connections |
| `oci_local_peering_gateway` | Manage local peering gateways |
| `oci_remote_peering_connection` | Manage remote peering connections |
| `oci_private_endpoint` | Manage private endpoints |
| `oci_public_ip` | Manage reserved public IPs |
| `oci_private_ip` | Manage secondary private IPs |
| `oci_network_firewall` | Manage OCI Network Firewalls |
| `oci_network_firewall_policy` | Manage Network Firewall policies |
| `oci_vtap` | Manage virtual test access points |
| `oci_capture_filter` | Manage VTAP capture filters |
| `oci_traffic_management_steering_policy` | Manage DNS traffic steering policies |
| `oci_fastconnect` | Manage FastConnect virtual circuits |
| `oci_cross_connect` | Manage cross-connect resources |

### Database

| Module | Description |
|---|---|
| `oci_autonomous_database` | Manage Autonomous Databases (ATP/ADW) |
| `oci_autonomous_database_clone` | Clone Autonomous Databases |
| `oci_autonomous_database_wallet` | Manage Autonomous Database wallets |
| `oci_db_system` | Manage DB Systems |
| `oci_db_backup` | Manage database backups |
| `oci_db_home` | Manage Database Homes |
| `oci_data_guard` | Manage Data Guard associations |
| `oci_mysql_db_system` | Manage MySQL Database Service systems |
| `oci_nosql_table` | Manage NoSQL Database tables |
| `oci_postgresql_db_system` | Manage PostgreSQL Database systems |
| `oci_exadata_infrastructure` | Manage Exadata Cloud Infrastructure |
| `oci_vm_cluster` | Manage Exadata VM clusters |
| `oci_pluggable_database` | Manage Pluggable Databases |
| `oci_external_database` | Manage external database connectors |
| `oci_database_migration` | Manage Database Migration Service |
| `oci_goldengate_deployment` | Manage GoldenGate deployments |
| `oci_goldengate_connection` | Manage GoldenGate connections |

### Identity and Access Management

| Module | Description |
|---|---|
| `oci_compartment` | Manage compartments |
| `oci_user` | Manage users |
| `oci_group` | Manage groups |
| `oci_dynamic_group` | Manage dynamic groups |
| `oci_policy` | Manage IAM policies |
| `oci_api_key` | Manage user API keys |
| `oci_identity_domain` | Manage Identity Domains |
| `oci_auth_token` | Manage user auth tokens |
| `oci_customer_secret_key` | Manage S3-compatible secret keys |
| `oci_smtp_credential` | Manage SMTP credentials |
| `oci_network_source` | Manage network source restrictions |
| `oci_tag_namespace` | Manage tag namespaces |
| `oci_tag` | Manage tags |
| `oci_tag_default` | Manage tag defaults |
| `oci_quota` | Manage compartment quotas |

### Storage

| Module | Description |
|---|---|
| `oci_volume` | Manage block volumes |
| `oci_volume_backup` | Manage volume backups |
| `oci_bucket` | Manage Object Storage buckets |
| `oci_object` | Manage Object Storage objects |
| `oci_preauthenticated_request` | Manage pre-authenticated requests |
| `oci_object_lifecycle_policy` | Manage Object Storage lifecycle policies |
| `oci_replication_policy` | Manage cross-region replication |
| `oci_retention_rule` | Manage Object Storage retention rules |
| `oci_file_system` | Manage File Storage file systems |
| `oci_mount_target` | Manage File Storage mount targets |
| `oci_export` | Manage File Storage exports |
| `oci_export_set` | Manage File Storage export sets |
| `oci_snapshot` | Manage File Storage snapshots |

### Container and Kubernetes

| Module | Description |
|---|---|
| `oci_oke_cluster` | Manage OKE Kubernetes clusters |
| `oci_oke_cluster_facts` | Gather OKE cluster facts |
| `oci_oke_node_pool` | Manage OKE node pools |
| `oci_oke_node_pool_facts` | Gather OKE node pool facts |
| `oci_container_instance` | Manage Container Instances |
| `oci_container_registry` | Manage Container Registry repositories |

### Security

| Module | Description |
|---|---|
| `oci_vault` | Manage vaults |
| `oci_vault_secret` | Manage vault secrets |
| `oci_key` | Manage encryption keys |
| `oci_certificate` | Manage OCI Certificates |
| `oci_waf` | Manage Web Application Firewalls |
| `oci_bastion` | Manage Bastion Service instances |
| `oci_cloud_guard` | Manage Cloud Guard targets |
| `oci_cloud_guard_detector_recipe` | Manage Cloud Guard detector recipes |
| `oci_cloud_guard_responder_recipe` | Manage Cloud Guard responder recipes |
| `oci_security_zone` | Manage Security Zones |
| `oci_vulnerability_scan` | Manage Vulnerability Scanning recipes |

### Observability

| Module | Description |
|---|---|
| `oci_alarm` | Manage monitoring alarms |
| `oci_alarm_suppression` | Manage alarm suppression windows |
| `oci_log_group` | Manage log groups |
| `oci_log` | Manage log resources |
| `oci_log_analytics_entity` | Manage Log Analytics entities |
| `oci_health_check` | Manage HTTP health check monitors |
| `oci_apm_domain` | Manage APM domains |
| `oci_service_connector` | Manage Service Connector Hub |
| `oci_management_agent` | Manage Management Agents |
| `oci_os_management` | Manage OS Management instances |
| `oci_notification_topic` | Manage notification topics |
| `oci_notification_subscription` | Manage notification subscriptions |
| `oci_events_rule` | Manage Events rules |

### DevOps

| Module | Description |
|---|---|
| `oci_devops_project` | Manage DevOps projects |
| `oci_devops_repository` | Manage DevOps code repositories |
| `oci_devops_build_pipeline` | Manage DevOps build pipelines |
| `oci_devops_deploy_pipeline` | Manage DevOps deployment pipelines |
| `oci_artifact_repository` | Manage Artifact Registry repositories |

### Serverless and Application Integration

| Module | Description |
|---|---|
| `oci_functions_application` | Manage Functions applications |
| `oci_functions_function` | Manage Functions functions |
| `oci_api_gateway` | Manage API Gateways |
| `oci_api_gateway_deployment` | Manage API Gateway deployments |
| `oci_streaming` | Manage Streaming streams |
| `oci_queue` | Manage Queue service queues |
| `oci_email_delivery` | Manage Email Delivery senders |
| `oci_integration_instance` | Manage Integration instances |
| `oci_visual_builder` | Manage Visual Builder instances |
| `oci_digital_assistant` | Manage Digital Assistant instances |

### AI and Machine Learning

| Module | Description |
|---|---|
| `oci_data_science_project` | Manage Data Science projects |
| `oci_data_science_notebook` | Manage Data Science notebook sessions |
| `oci_data_science_model` | Manage Data Science models |
| `oci_data_science_model_deployment` | Manage Data Science model deployments |
| `oci_ai_vision_project` | Manage AI Vision projects |
| `oci_ai_language_project` | Manage AI Language projects |
| `oci_ai_speech_transcription` | Manage AI Speech transcription jobs |
| `oci_ai_anomaly_detection` | Manage AI Anomaly Detection projects |
| `oci_generative_ai_model` | Manage Generative AI models |
| `oci_generative_ai_endpoint` | Manage Generative AI endpoints |

### Data and Analytics

| Module | Description |
|---|---|
| `oci_data_integration_workspace` | Manage Data Integration workspaces |
| `oci_data_catalog` | Manage Data Catalog instances |
| `oci_data_flow_application` | Manage Data Flow applications |
| `oci_data_safe` | Manage Data Safe configurations |
| `oci_data_labeling_dataset` | Manage Data Labeling datasets |
| `oci_analytics_instance` | Manage Analytics Cloud instances |
| `oci_big_data_service` | Manage Big Data Service clusters |
| `oci_opensearch_cluster` | Manage OpenSearch clusters |

### Migration and Governance

| Module | Description |
|---|---|
| `oci_budget` | Manage budgets |
| `oci_resource_manager_stack` | Manage Resource Manager stacks |
| `oci_cloud_migration` | Manage Cloud Migrations |
| `oci_ocb_inventory` | Manage Oracle Cloud Bridge inventories |

### Inventory Plugin

| Plugin | Description |
|---|---|
| `oci_inventory` | Dynamic inventory plugin for OCI compute instances |

## Usage Examples

### Create a compute instance

```yaml
- name: Launch a compute instance
  oracle.oci.oci_instance:
    compartment_id: "ocid1.compartment.oc1..example"
    availability_domain: "Uocm:US-ASHBURN-AD-1"
    display_name: "my-instance"
    shape: "VM.Standard.E4.Flex"
    shape_config:
      ocpus: 2
      memory_in_gbs: 32
    source_details:
      source_type: image
      image_id: "ocid1.image.oc1..example"
    create_vnic_details:
      subnet_id: "ocid1.subnet.oc1..example"
    state: present
```

### Create a VCN with subnet

```yaml
- name: Create a VCN
  oracle.oci.oci_vcn:
    compartment_id: "ocid1.compartment.oc1..example"
    display_name: "my-vcn"
    cidr_blocks:
      - "10.0.0.0/16"
    state: present
  register: vcn

- name: Create a subnet
  oracle.oci.oci_subnet:
    compartment_id: "ocid1.compartment.oc1..example"
    vcn_id: "{{ vcn.resource.id }}"
    display_name: "my-subnet"
    cidr_block: "10.0.1.0/24"
    state: present
```

### Use the dynamic inventory

Create an inventory file `oci.yml`:

```yaml
plugin: oracle.oci.oci_inventory
regions:
  - us-ashburn-1
compartments:
  - ocid1.compartment.oc1..example
keyed_groups:
  - key: shape
    prefix: shape
  - key: region
    prefix: region
```

```bash
ansible-inventory -i oci.yml --list
```

## Testing

Run linting and sanity checks:

```bash
pip install ansible-core>=2.16 ansible-lint yamllint flake8
yamllint -c .yamllint .
flake8 plugins/ --max-line-length=120 --ignore=E402,W503
ansible-lint --strict
```

Run sanity tests (must be checked out as `ansible_collections/oracle/oci/`):

```bash
ansible-test sanity --python 3.12 -v
```

Run unit tests:

```bash
pip install pytest oci
pytest tests/unit/ -v --tb=short
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write your module following the existing patterns in `plugins/modules/`
4. Add unit tests in `tests/unit/`
5. Run sanity and lint checks
6. Submit a pull request

## License

GNU General Public License v3.0 or later.

See [COPYING](COPYING) for the full license text.
