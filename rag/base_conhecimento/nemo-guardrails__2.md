---
tecnologia: NeMo Guardrails
categoria: seguranca
url_fonte: https://docs.nvidia.com/nemo/guardrails/latest/introduction.html
titulo: Overview | NVIDIA NeMo Guardrails Library Developer Guide
---
The NVIDIA NeMo Guardrails library is an open-source Python package enabling developers to add safety mechanisms to large language model applications. As described in the documentation, it functions as an open-source Python package for adding programmable guardrails to LLM-based applications.

The library operates through several core mechanisms. It employs input, retrieval, dialog, execution, and output rails that activate at different interaction stages, so a policy can be enforced at the point in the pipeline where it is most effective. Configuration occurs via YAML files defining models, prompts, and runtime settings, while Colang, a specialized language, manages conversational flows and event-driven behavior. Python functions and external APIs provide extensibility through custom actions.

Key capabilities include content safety implementation, jailbreak protection, topic control, and personally identifiable information detection. Organizations can leverage LLM self-checking, integrate NVIDIA safety models, or connect third-party moderation services, which means the same rail structure can be backed by different detection engines depending on cost, latency, and accuracy requirements.

The system supports multiple deployment patterns: direct Python integration via the SDK, HTTP deployment through a FastAPI server, or framework-specific integrations with tools like LangChain. This gives teams a choice between embedding guardrails in the application process and running them as a separate service in front of a model endpoint.

The library maintains consistency across development and production environments. Configurations developed locally remain compatible when deployed via the production microservice, eliminating the need to rewrite applications or modify model backends. This architectural flexibility allows teams to implement policy enforcement and safety checks while preserving application architecture choices and maintaining developer control over the guardrailing workflow at multiple processing stages. For governance, this means the rules that were tested during development are the same rules that run in production.
