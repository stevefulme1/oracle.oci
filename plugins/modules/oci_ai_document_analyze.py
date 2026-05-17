# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for OCI AI Document analysis (OCR)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_document_analyze
short_description: Analyze documents using OCI AI Document Understanding
description:
    - Perform OCR, table extraction, key-value extraction, and document classification
      using the OCI AI Document Understanding service.
    - This is an B(action) module that calls AI inference APIs and returns results.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.ai_document.AIServiceDocumentClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
        required: true
    document_source:
        description:
            - The source type for the document.
        type: str
        required: true
        choices:
            - url
            - base64
            - object_storage
    document_url:
        description:
            - The URL of the document to analyze.
            - Required when I(document_source=url).
        type: str
    document_data:
        description:
            - The base64-encoded document data.
            - Required when I(document_source=base64).
            - This is document content, not a secret, so it is not masked in logs.
        type: str
    namespace_name:
        description:
            - The Object Storage namespace.
            - Required when I(document_source=object_storage).
        type: str
    bucket_name:
        description:
            - The Object Storage bucket name.
            - Required when I(document_source=object_storage).
        type: str
    object_name:
        description:
            - The Object Storage object name.
            - Required when I(document_source=object_storage).
        type: str
    analysis_type:
        description:
            - The type of document analysis to perform.
        type: str
        required: true
        choices:
            - text_extraction
            - table_extraction
            - key_value_extraction
            - document_classification
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Extract text from a document in Object Storage
  oracle.oci.oci_ai_document_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    document_source: object_storage
    namespace_name: "mytenancy"
    bucket_name: "documents"
    object_name: "invoice.pdf"
    analysis_type: text_extraction
  register: ocr_result

- name: Extract tables from a base64-encoded document
  oracle.oci.oci_ai_document_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    document_source: base64
    document_data: "JVBERi0xLjQK..."
    analysis_type: table_extraction

- name: Extract key-value pairs from a document URL
  oracle.oci.oci_ai_document_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    document_source: url
    document_url: "https://example.com/form.pdf"
    analysis_type: key_value_extraction

- name: Classify a document
  oracle.oci.oci_ai_document_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    document_source: object_storage
    namespace_name: "mytenancy"
    bucket_name: "documents"
    object_name: "document.pdf"
    analysis_type: document_classification

- name: Check mode - preview request
  oracle.oci.oci_ai_document_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    document_source: url
    document_url: "https://example.com/form.pdf"
    analysis_type: text_extraction
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured document analysis results.
    returned: success
    type: dict
    contains:
        pages:
            description: List of per-page analysis results.
            type: list
        detected_document_types:
            description: Detected document types with confidence scores.
            type: list
        text:
            description: All extracted text concatenated.
            type: str
        tables:
            description: List of extracted tables.
            type: list
        key_values:
            description: List of extracted key-value pairs.
            type: list
raw_response:
    description: The full API response as a dictionary.
    returned: success
    type: dict
request_payload:
    description: The request payload that was (or would be) sent. Returned in check mode.
    returned: check_mode
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from oci.ai_document import AIServiceDocumentClient
    from oci.ai_document.models import (
        AnalyzeDocumentDetails,
        DocumentTextExtractionFeature,
        DocumentTableExtractionFeature,
        DocumentKeyValueExtractionFeature,
        DocumentClassificationFeature,
        InlineDocumentDetails,
        ObjectStorageLocations,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.oracle.oci.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.oracle.oci.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.oracle.oci.plugins.module_utils.oci_wait import call_with_retry


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str", required=True),
        document_source=dict(type="str", required=True, choices=["url", "base64", "object_storage"]),
        document_url=dict(type="str"),
        document_data=dict(type="str"),
        namespace_name=dict(type="str"),
        bucket_name=dict(type="str"),
        object_name=dict(type="str"),
        analysis_type=dict(
            type="str", required=True,
            choices=["text_extraction", "table_extraction", "key_value_extraction", "document_classification"],
        ),
    )
    module_args.update(OCI_COMMON_ARGS)
    return module_args


def to_dict(resource):
    """Recursively convert an OCI model object to a plain dict."""
    if resource is None:
        return {}
    if isinstance(resource, dict):
        return {k: to_dict(v) for k, v in resource.items()}
    if isinstance(resource, list):
        return [to_dict(i) for i in resource]
    if hasattr(resource, "__dict__"):
        result = {}
        for key, value in resource.__dict__.items():
            if key.startswith("_"):
                continue
            result[key] = to_dict(value)
        return result
    return resource


def _build_document_details(params):
    """Build document details based on source type."""
    source = params["document_source"]

    if source == "base64":
        return InlineDocumentDetails(data=params["document_data"])
    elif source == "object_storage":
        return InlineDocumentDetails(
            source="OBJECT_STORAGE",
            namespace_name=params["namespace_name"],
            bucket_name=params["bucket_name"],
            object_name=params["object_name"],
        )
    else:
        # URL source
        return InlineDocumentDetails(
            source="URL",
            source_image_url=params["document_url"],
        )


def _build_features(analysis_type):
    """Build the analysis feature list."""
    feature_map = {
        "text_extraction": DocumentTextExtractionFeature(),
        "table_extraction": DocumentTableExtractionFeature(),
        "key_value_extraction": DocumentKeyValueExtractionFeature(),
        "document_classification": DocumentClassificationFeature(),
    }
    return [feature_map[analysis_type]]


def _extract_pages(response_data):
    """Extract per-page results from the response."""
    pages = []
    for page in getattr(response_data, "pages", []):
        page_info = {
            "page_number": getattr(page, "page_number", 0),
            "width": getattr(page, "width", None),
            "height": getattr(page, "height", None),
        }

        # Text lines
        lines = []
        for line in getattr(page, "lines", []):
            lines.append({
                "text": getattr(line, "text", ""),
                "confidence": getattr(line, "confidence", 0.0),
                "bounding_polygon": to_dict(getattr(line, "bounding_polygon", None)),
            })
        page_info["lines"] = lines

        # Words
        words = []
        for word in getattr(page, "words", []):
            words.append({
                "text": getattr(word, "text", ""),
                "confidence": getattr(word, "confidence", 0.0),
            })
        page_info["words"] = words

        # Tables
        tables = []
        for table in getattr(page, "tables", []):
            rows = []
            for row in getattr(table, "body_rows", []) or getattr(table, "rows", []):
                cells = []
                for cell in getattr(row, "cells", []):
                    cells.append({
                        "text": getattr(cell, "text", ""),
                        "row_index": getattr(cell, "row_index", 0),
                        "column_index": getattr(cell, "column_index", 0),
                        "confidence": getattr(cell, "confidence", 0.0),
                    })
                rows.append(cells)
            tables.append({
                "row_count": getattr(table, "row_count", 0),
                "column_count": getattr(table, "column_count", 0),
                "rows": rows,
            })
        page_info["tables"] = tables

        # Document fields (key-value)
        fields = []
        for field in getattr(page, "document_fields", []):
            field_info = {
                "field_type": getattr(field, "field_type", ""),
            }
            label = getattr(field, "field_label", None)
            if label:
                field_info["label"] = getattr(label, "name", "")
            value = getattr(field, "field_value", None)
            if value:
                field_info["value"] = getattr(value, "value", "")
                field_info["value_type"] = getattr(value, "value_type", "")
                field_info["confidence"] = getattr(value, "confidence", 0.0)
            fields.append(field_info)
        page_info["document_fields"] = fields

        pages.append(page_info)
    return pages


def _extract_full_text(pages):
    """Concatenate all text lines from all pages."""
    all_text = []
    for page in pages:
        for line in page.get("lines", []):
            if line.get("text"):
                all_text.append(line["text"])
    return "\n".join(all_text)


def _extract_tables(pages):
    """Collect all tables from all pages."""
    tables = []
    for page in pages:
        for table in page.get("tables", []):
            tables.append(table)
    return tables


def _extract_key_values(pages):
    """Collect all key-value pairs from all pages."""
    key_values = []
    for page in pages:
        for field in page.get("document_fields", []):
            key_values.append(field)
    return key_values


def _extract_document_types(response_data):
    """Extract detected document types."""
    doc_types = []
    for dt in getattr(response_data, "detected_document_types", []):
        doc_types.append({
            "document_type": getattr(dt, "document_type", ""),
            "confidence": getattr(dt, "confidence", 0.0),
        })
    return doc_types


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("document_source", "url", ("document_url",)),
            ("document_source", "base64", ("document_data",)),
            ("document_source", "object_storage", ("namespace_name", "bucket_name", "object_name")),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    analysis_type = params["analysis_type"]

    payload_info = {
        "compartment_id": params["compartment_id"],
        "document_source": params["document_source"],
        "analysis_type": analysis_type,
    }
    if params["document_source"] == "url":
        payload_info["document_url"] = params["document_url"]
    elif params["document_source"] == "object_storage":
        payload_info["namespace_name"] = params["namespace_name"]
        payload_info["bucket_name"] = params["bucket_name"]
        payload_info["object_name"] = params["object_name"]
    elif params["document_source"] == "base64":
        payload_info["document_data_length"] = len(params.get("document_data") or "")

    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_info,
            result={
                "pages": [],
                "detected_document_types": [],
                "text": "",
                "tables": [],
                "key_values": [],
            },
            raw_response={},
        )

    client = create_service_client(module, AIServiceDocumentClient)

    try:
        document_details = _build_document_details(params)
        features = _build_features(analysis_type)

        analyze_details = AnalyzeDocumentDetails(
            compartment_id=params["compartment_id"],
            document=document_details,
            features=features,
        )

        response = call_with_retry(client.analyze_document, analyze_details)
        response_data = response.data

        pages = _extract_pages(response_data)
        detected_document_types = _extract_document_types(response_data)
        full_text = _extract_full_text(pages)
        tables = _extract_tables(pages)
        key_values = _extract_key_values(pages)

        result = {
            "pages": pages,
            "detected_document_types": detected_document_types,
            "text": full_text,
            "tables": tables,
            "key_values": key_values,
        }

        module.exit_json(
            changed=False,
            result=result,
            raw_response=to_dict(response_data),
        )
    except ServiceError as e:
        module.fail_json(
            msg=f"OCI AI Document analysis failed: {e.message}",
            status=e.status,
            code=e.code,
            request_payload=payload_info,
        )


if __name__ == "__main__":
    main()
