# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for OCI AI Language analysis."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_ai_language_analyze
short_description: Run NLP analysis on text using OCI AI Language
description:
    - Perform natural language processing analysis on text including sentiment analysis,
      entity extraction, key phrase detection, language detection, and translation.
    - This is an B(action) module that calls AI inference APIs and returns results.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.ai_language.AIServiceLanguageClient).
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
        required: true
    text:
        description:
            - The text to analyze.
            - Can be a single string or a list of strings for batch processing.
        type: raw
        required: true
    analysis_type:
        description:
            - The type of NLP analysis to perform.
        type: str
        required: true
        choices:
            - sentiment
            - entities
            - key_phrases
            - language_detection
            - translation
    target_language:
        description:
            - The target language code for translation (e.g., "es", "fr", "de").
            - Required when I(analysis_type=translation).
        type: str
extends_documentation_fragment:
    - oracle.oci.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Analyze sentiment of text
  oracle.oci.oci_ai_language_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    text: "The product is excellent and the support team was very helpful."
    analysis_type: sentiment
  register: sentiment_result

- name: Extract entities from multiple texts
  oracle.oci.oci_ai_language_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    text:
      - "Oracle Corporation is headquartered in Austin, Texas."
      - "John Smith works at Red Hat in Raleigh, North Carolina."
    analysis_type: entities

- name: Translate text to Spanish
  oracle.oci.oci_ai_language_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    text: "Hello, how are you today?"
    analysis_type: translation
    target_language: "es"

- name: Check mode - preview request
  oracle.oci.oci_ai_language_analyze:
    compartment_id: "ocid1.compartment.oc1..example"
    text: "Some text to analyze"
    analysis_type: sentiment
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured analysis results.
    returned: success
    type: dict
    contains:
        results:
            description: List of analysis results for each input text.
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
    from oci.ai_language import AIServiceLanguageClient
    from oci.ai_language.models import (
        BatchDetectLanguageSentimentsDetails,
        BatchDetectLanguageEntitiesDetails,
        BatchDetectLanguageKeyPhrasesDetails,
        BatchDetectLanguageTextClassificationDetails,
        BatchLanguageTranslationDetails,
        TextDocument,
        TranslationDocumentDetails,
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
        text=dict(type="raw", required=True),
        analysis_type=dict(
            type="str", required=True,
            choices=["sentiment", "entities", "key_phrases", "language_detection", "translation"],
        ),
        target_language=dict(type="str"),
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


def _normalize_text(text_input):
    """Ensure text is a list of strings."""
    if isinstance(text_input, str):
        return [text_input]
    if isinstance(text_input, list):
        return [str(t) for t in text_input]
    return [str(text_input)]


def _build_text_documents(texts):
    """Build TextDocument list with sequential keys."""
    return [TextDocument(key=str(i), text=t) for i, t in enumerate(texts)]


def _build_translation_documents(texts, target_language):
    """Build TranslationDocumentDetails list."""
    return [
        TranslationDocumentDetails(key=str(i), text=t, language_code=target_language)
        for i, t in enumerate(texts)
    ]


def _extract_sentiment_results(response_data):
    """Extract structured sentiment analysis results."""
    results = []
    for doc in getattr(response_data, "documents", []):
        aspects = []
        for aspect in getattr(doc, "aspects", []):
            aspects.append({
                "text": getattr(aspect, "text", ""),
                "sentiment": getattr(aspect, "sentiment", ""),
                "scores": to_dict(getattr(aspect, "scores", {})),
            })
        results.append({
            "key": getattr(doc, "key", ""),
            "document_sentiment": getattr(doc, "document_sentiment", ""),
            "document_scores": to_dict(getattr(doc, "document_scores", {})),
            "aspects": aspects,
        })
    return results


def _extract_entity_results(response_data):
    """Extract structured entity analysis results."""
    results = []
    for doc in getattr(response_data, "documents", []):
        entities = []
        for entity in getattr(doc, "entities", []):
            entities.append({
                "text": getattr(entity, "text", ""),
                "type": getattr(entity, "type", ""),
                "sub_type": getattr(entity, "sub_type", None),
                "score": getattr(entity, "score", 0.0),
                "offset": getattr(entity, "offset", None),
                "length": getattr(entity, "length", None),
            })
        results.append({
            "key": getattr(doc, "key", ""),
            "entities": entities,
        })
    return results


def _extract_key_phrase_results(response_data):
    """Extract structured key phrase results."""
    results = []
    for doc in getattr(response_data, "documents", []):
        phrases = []
        for phrase in getattr(doc, "key_phrases", []):
            phrases.append({
                "text": getattr(phrase, "text", ""),
                "score": getattr(phrase, "score", 0.0),
            })
        results.append({
            "key": getattr(doc, "key", ""),
            "key_phrases": phrases,
        })
    return results


def _extract_language_results(response_data):
    """Extract structured language detection results."""
    results = []
    for doc in getattr(response_data, "documents", []):
        languages = []
        for lang in getattr(doc, "languages", []):
            languages.append({
                "name": getattr(lang, "name", ""),
                "code": getattr(lang, "code", ""),
                "score": getattr(lang, "score", 0.0),
            })
        results.append({
            "key": getattr(doc, "key", ""),
            "languages": languages,
        })
    return results


def _extract_translation_results(response_data):
    """Extract structured translation results."""
    results = []
    for doc in getattr(response_data, "documents", []):
        results.append({
            "key": getattr(doc, "key", ""),
            "translated_text": getattr(doc, "translated_text", ""),
            "source_language_code": getattr(doc, "source_language_code", None),
            "target_language_code": getattr(doc, "target_language_code", None),
        })
    return results


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
        required_if=[
            ("analysis_type", "translation", ("target_language",)),
        ],
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    analysis_type = params["analysis_type"]
    texts = _normalize_text(params["text"])
    compartment_id = params["compartment_id"]

    # Build payload description for check mode
    payload_info = {
        "compartment_id": compartment_id,
        "analysis_type": analysis_type,
        "documents": [{"key": str(i), "text": t} for i, t in enumerate(texts)],
    }
    if analysis_type == "translation":
        payload_info["target_language"] = params["target_language"]

    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_info,
            result={"results": []},
            raw_response={},
        )

    client = create_service_client(module, AIServiceLanguageClient)

    try:
        if analysis_type == "sentiment":
            documents = _build_text_documents(texts)
            details = BatchDetectLanguageSentimentsDetails(
                compartment_id=compartment_id,
                documents=documents,
            )
            response = call_with_retry(client.batch_detect_language_sentiments, details)
            result_data = _extract_sentiment_results(response.data)

        elif analysis_type == "entities":
            documents = _build_text_documents(texts)
            details = BatchDetectLanguageEntitiesDetails(
                compartment_id=compartment_id,
                documents=documents,
            )
            response = call_with_retry(client.batch_detect_language_entities, details)
            result_data = _extract_entity_results(response.data)

        elif analysis_type == "key_phrases":
            documents = _build_text_documents(texts)
            details = BatchDetectLanguageKeyPhrasesDetails(
                compartment_id=compartment_id,
                documents=documents,
            )
            response = call_with_retry(client.batch_detect_language_key_phrases, details)
            result_data = _extract_key_phrase_results(response.data)

        elif analysis_type == "language_detection":
            documents = _build_text_documents(texts)
            details = BatchDetectLanguageTextClassificationDetails(
                compartment_id=compartment_id,
                documents=documents,
            )
            response = call_with_retry(client.batch_detect_language_text_classification, details)
            result_data = _extract_language_results(response.data)

        elif analysis_type == "translation":
            documents = _build_translation_documents(texts, params["target_language"])
            details = BatchLanguageTranslationDetails(
                compartment_id=compartment_id,
                documents=documents,
                target_language_code=params["target_language"],
            )
            response = call_with_retry(client.batch_language_translation, details)
            result_data = _extract_translation_results(response.data)

        else:
            module.fail_json(msg=f"Unsupported analysis_type: {analysis_type}")
            return

        module.exit_json(
            changed=False,
            result={"results": result_data},
            raw_response=to_dict(response.data),
        )
    except ServiceError as e:
        module.fail_json(
            msg=f"OCI AI Language analysis failed: {e.message}",
            status=e.status,
            code=e.code,
            request_payload=payload_info,
        )


if __name__ == "__main__":
    main()
