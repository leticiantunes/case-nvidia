---
tecnologia: NeMo Guardrails
categoria: seguranca
url_fonte: https://github.com/NVIDIA/NeMo-Guardrails
titulo: NVIDIA NeMo Guardrails Library
---
NVIDIA NeMo Guardrails is an open-source toolkit designed for developers building LLM-based applications who need to implement programmable guardrails between their application code and large language models. The library addresses critical safety and security concerns by enabling developers to control LLM outputs through specific behavioral constraints, rather than relying on prompt engineering alone.

The toolkit supports five main types of guardrails operating at different stages of the LLM pipeline. Input rails process user messages before they reach the model, potentially rejecting or altering content. Dialog rails influence how the LLM is prompted using Colang, a domain-specific language for modeling conversational flows. Retrieval rails filter chunks in retrieval-augmented generation scenarios. Execution rails protect custom tool interactions, which matters for agents that can call external functions. Output rails examine and potentially reject or modify model-generated responses before they are returned to the user.

Key capabilities include protecting against jailbreaks and prompt injections, maintaining topical focus for domain-specific assistants, enforcing conversational paths that follow standard operating procedures, and integrating multiple safety approaches including fact-checking and hallucination detection. The library provides built-in guardrails for common scenarios while allowing custom implementations through Python actions, so organization-specific policy can be encoded directly.

Colang, a Python-like modeling language, enables flexible yet controllable dialogue design, supporting both version 1.0 (the default) and 2.0. The system works with multiple LLM providers including OpenAI, open-source models, and NVIDIA endpoints, so the same guardrail configuration can be reused as the underlying model changes.

Primary use cases encompass question-answering over documents with fact-checking, domain-specific chatbots that must stay on topic, LLM endpoints that require an added safety layer, and LangChain chain integration for existing applications.
