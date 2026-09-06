---
tecnologia: NVIDIA Triton Inference Server
categoria: inferencia
url_fonte: https://developer.nvidia.com/triton-inference-server
titulo: Dynamo-Triton Open-Source Software | NVIDIA Developer
---
NVIDIA Dynamo-Triton, formerly NVIDIA Triton Inference Server, enables deployment of AI models across major frameworks, including TensorRT, PyTorch, ONNX, OpenVINO, Python, and RAPIDS FIL. It solves the problem of serving models that were trained in different frameworks behind a single, consistent production inference layer.

It delivers high performance with dynamic batching, concurrent execution, and optimized configurations. Dynamo-Triton supports real-time, batched, ensemble, and audio/video streaming workloads and runs on NVIDIA GPUs, non-NVIDIA accelerators, x86, and ARM CPUs. Dynamic batching groups incoming requests together to raise throughput, while concurrent execution lets multiple models or multiple instances of a model share the same accelerator, improving utilization instead of leaving hardware idle between requests.

Open source and compatible with DevOps and MLOps workflows, Dynamo-Triton integrates with Kubernetes for scaling and Prometheus for monitoring. It works across cloud and on-premises AI platforms and, as part of NVIDIA AI Enterprise, provides a secure, production-ready environment with stable APIs and support for AI deployment.

For large language model use cases, NVIDIA also offers NVIDIA Dynamo, designed for LLM inference and multi-mode deployment. It complements Dynamo-Triton with LLM-specific optimizations such as disaggregated serving, prefix caching, and key-value caching to storage. These techniques target the specific cost structure of LLM serving, where repeated prompt prefixes and large key-value caches dominate memory and latency.

Modern deep learning systems often require the use of multiple models in a pipeline and the use of accelerated pre- and post-processing steps. Triton Inference Server enables efficient implementation through model ensembles and business logic scripting, so an entire pipeline can run inside the server rather than being stitched together with extra network hops in application code.

Linux-based Triton Inference Server containers for x86 and Arm are available on NVIDIA NGC, with client libraries and binary releases for Windows and NVIDIA Jetson JetPack available on GitHub.
