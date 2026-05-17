# -*- coding: utf-8 -*-
# Copyright (c) 2024, Oracle and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for invoking OCI Generative AI inference."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: oci_generative_ai_inference
short_description: Send prompts to OCI Generative AI models
description:
    - Invoke OCI Generative AI models to generate text, chat responses, summaries, or embeddings.
    - This is an B(action) module that calls AI inference APIs and returns results.
      It does not manage infrastructure resources.
    - Uses the OCI Python SDK C(oci.generative_ai_inference.GenerativeAiInferenceClient).
    - Supports both Cohere and Llama model families via the I(model_type) parameter.
version_added: "1.0.0"
author:
    - Oracle (@oracle)
options:
    compartment_id:
        description:
            - The OCID of the compartment.
        type: str
        required: true
    model_id:
        description:
            - The OCID of the model or model endpoint to invoke.
        type: str
        required: true
    model_type:
        description:
            - The model family to use, which determines the request format.
        type: str
        required: true
        choices:
            - cohere
            - llama
    inference_type:
        description:
            - The type of inference to perform.
        type: str
        default: generate
        choices:
            - generate
            - chat
            - summarize
            - embed
    prompt:
        description:
            - The input prompt text to send to the model.
        type: str
        required: true
    system_prompt:
        description:
            - System prompt for chat inference. Sets the model behavior context.
            - Only used when I(inference_type=chat).
        type: str
    max_tokens:
        description:
            - Maximum number of tokens to generate in the response.
        type: int
        default: 256
    temperature:
        description:
            - Sampling temperature for generation. Higher values produce more random output.
        type: float
        default: 0.7
extends_documentation_fragment:
    - stevefulme1.oci_cloud.oci_common
requirements:
    - "python >= 3.8"
    - "oci >= 2.90.0"
"""

EXAMPLES = r"""
- name: Generate text with a Cohere model
  stevefulme1.oci_cloud.oci_generative_ai_inference:
    compartment_id: "ocid1.compartment.oc1..example"
    model_id: "ocid1.generativeaimodel.oc1..example"
    model_type: cohere
    inference_type: generate
    prompt: "Explain Ansible automation in one paragraph."
    max_tokens: 512
    temperature: 0.5
  register: genai_result

- name: Chat with a Llama model
  stevefulme1.oci_cloud.oci_generative_ai_inference:
    compartment_id: "ocid1.compartment.oc1..example"
    model_id: "ocid1.generativeaimodel.oc1..example"
    model_type: llama
    inference_type: chat
    prompt: "What are the benefits of infrastructure as code?"
    system_prompt: "You are a DevOps expert."
    max_tokens: 1024
  register: chat_result

- name: Check mode - preview the request payload without calling the API
  stevefulme1.oci_cloud.oci_generative_ai_inference:
    compartment_id: "ocid1.compartment.oc1..example"
    model_id: "ocid1.generativeaimodel.oc1..example"
    model_type: cohere
    prompt: "Hello world"
  check_mode: true
"""

RETURN = r"""
result:
    description: Structured inference results.
    returned: success
    type: dict
    contains:
        text:
            description: The generated text.
            type: str
        finish_reason:
            description: The reason generation stopped.
            type: str
        token_count:
            description: Number of tokens in the response.
            type: int
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
    from oci.generative_ai_inference import GenerativeAiInferenceClient
    from oci.generative_ai_inference.models import (
        GenerateTextDetails,
        CohereLlmInferenceRequest,
        LlamaLlmInferenceRequest,
        ChatDetails,
        CohereChatRequest,
        LlamaChatRequest,
        SummarizeTextDetails,
        EmbedTextDetails,
        OnDemandServingMode,
        DedicatedServingMode,
    )
    from oci.exceptions import ServiceError

    HAS_OCI_SDK = True
except ImportError:
    HAS_OCI_SDK = False

from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_common import (
    OCI_COMMON_ARGS,
)
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_auth import create_service_client
from ansible_collections.stevefulme1.oci_cloud.plugins.module_utils.oci_wait import call_with_retry


def get_module_args():
    module_args = dict(
        compartment_id=dict(type="str", required=True),
        model_id=dict(type="str", required=True),
        model_type=dict(type="str", required=True, choices=["cohere", "llama"]),
        inference_type=dict(
            type="str", default="generate",
            choices=["generate", "chat", "summarize", "embed"],
        ),
        prompt=dict(type="str", required=True),
        system_prompt=dict(type="str"),
        max_tokens=dict(type="int", default=256, no_log=False),
        temperature=dict(type="float", default=0.7),
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


def _get_serving_mode(model_id):
    """Return the appropriate serving mode based on model ID format."""
    if "endpoint" in model_id.lower():
        return DedicatedServingMode(endpoint_id=model_id)
    return OnDemandServingMode(model_id=model_id)


def _build_generate_payload(params):
    """Build a GenerateTextDetails payload."""
    model_type = params["model_type"]
    serving_mode = _get_serving_mode(params["model_id"])

    if model_type == "cohere":
        inference_request = CohereLlmInferenceRequest(
            prompt=params["prompt"],
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            is_stream=False,
        )
    else:
        inference_request = LlamaLlmInferenceRequest(
            prompt=params["prompt"],
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
        )

    return GenerateTextDetails(
        compartment_id=params["compartment_id"],
        serving_mode=serving_mode,
        inference_request=inference_request,
    )


def _build_chat_payload(params):
    """Build a ChatDetails payload."""
    model_type = params["model_type"]
    serving_mode = _get_serving_mode(params["model_id"])

    if model_type == "cohere":
        chat_request = CohereChatRequest(
            message=params["prompt"],
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            is_stream=False,
        )
        if params.get("system_prompt"):
            chat_request.preamble_override = params["system_prompt"]
    else:
        messages = []
        if params.get("system_prompt"):
            messages.append({"role": "system", "content": [{"type": "TEXT", "text": params["system_prompt"]}]})
        messages.append({"role": "user", "content": [{"type": "TEXT", "text": params["prompt"]}]})
        chat_request = LlamaChatRequest(
            messages=messages,
            max_tokens=params["max_tokens"],
            temperature=params["temperature"],
            is_stream=False,
        )

    return ChatDetails(
        compartment_id=params["compartment_id"],
        serving_mode=serving_mode,
        chat_request=chat_request,
    )


def _build_summarize_payload(params):
    """Build a SummarizeTextDetails payload."""
    serving_mode = _get_serving_mode(params["model_id"])

    return SummarizeTextDetails(
        compartment_id=params["compartment_id"],
        serving_mode=serving_mode,
        input=params["prompt"],
        temperature=params["temperature"],
    )


def _build_embed_payload(params):
    """Build an EmbedTextDetails payload."""
    serving_mode = _get_serving_mode(params["model_id"])

    return EmbedTextDetails(
        compartment_id=params["compartment_id"],
        serving_mode=serving_mode,
        inputs=[params["prompt"]],
    )


def _extract_generate_result(response_data):
    """Extract structured result from generate_text response."""
    generated_texts = getattr(response_data, "generated_texts", None)
    if generated_texts and len(generated_texts) > 0:
        # generated_texts is a list of lists for Cohere, or a list for Llama
        texts = generated_texts[0] if isinstance(generated_texts[0], list) else generated_texts
        if texts and len(texts) > 0:
            item = texts[0]
            return {
                "text": getattr(item, "text", str(item)),
                "finish_reason": getattr(item, "finish_reason", None),
                "token_count": getattr(item, "token_count", None),
            }
    # Fallback: attempt to find text from inference_response
    inference_response = getattr(response_data, "inference_response", response_data)
    gen_texts = getattr(inference_response, "generated_texts", [])
    if gen_texts:
        first_group = gen_texts[0] if isinstance(gen_texts[0], list) else gen_texts
        if first_group:
            item = first_group[0]
            return {
                "text": getattr(item, "text", str(item)),
                "finish_reason": getattr(item, "finish_reason", None),
                "token_count": getattr(item, "token_count", None),
            }
    return {"text": "", "finish_reason": None, "token_count": 0}


def _extract_chat_result(response_data):
    """Extract structured result from chat response."""
    chat_response = getattr(response_data, "chat_response", response_data)
    text = getattr(chat_response, "text", None) or getattr(chat_response, "message", None) or ""
    if hasattr(text, "content"):
        text = text.content
    if isinstance(text, list):
        text = " ".join(str(t) for t in text)
    return {
        "text": str(text),
        "finish_reason": getattr(chat_response, "finish_reason", None),
        "token_count": getattr(chat_response, "token_count", None),
    }


def _extract_summarize_result(response_data):
    """Extract structured result from summarize response."""
    return {
        "text": getattr(response_data, "summary", ""),
        "finish_reason": "complete",
        "token_count": None,
    }


def _extract_embed_result(response_data):
    """Extract structured result from embed response."""
    embeddings = getattr(response_data, "embeddings", [])
    return {
        "text": "",
        "finish_reason": "complete",
        "token_count": None,
        "embeddings": embeddings,
    }


def main():
    module = AnsibleModule(
        argument_spec=get_module_args(),
        supports_check_mode=True,
    )

    if not HAS_OCI_SDK:
        module.fail_json(msg="The 'oci' Python SDK is required. Install with: pip install oci")

    params = module.params
    inference_type = params["inference_type"]

    # Build request payload
    builders = {
        "generate": _build_generate_payload,
        "chat": _build_chat_payload,
        "summarize": _build_summarize_payload,
        "embed": _build_embed_payload,
    }
    payload = builders[inference_type](params)
    payload_dict = to_dict(payload)

    # Check mode: return what would be sent
    if module.check_mode:
        module.exit_json(
            changed=False,
            request_payload=payload_dict,
            result={"text": "", "finish_reason": None, "token_count": None},
            raw_response={},
        )

    client = create_service_client(module, GenerativeAiInferenceClient)

    try:
        api_methods = {
            "generate": client.generate_text,
            "chat": client.chat,
            "summarize": client.summarize_text,
            "embed": client.embed_text,
        }
        response = call_with_retry(api_methods[inference_type], payload)
        response_data = response.data

        extractors = {
            "generate": _extract_generate_result,
            "chat": _extract_chat_result,
            "summarize": _extract_summarize_result,
            "embed": _extract_embed_result,
        }
        result = extractors[inference_type](response_data)

        module.exit_json(
            changed=False,
            result=result,
            raw_response=to_dict(response_data),
        )
    except ServiceError as e:
        module.fail_json(
            msg=f"OCI Generative AI inference failed: {e.message}",
            status=e.status,
            code=e.code,
            request_payload=payload_dict,
        )


if __name__ == "__main__":
    main()
