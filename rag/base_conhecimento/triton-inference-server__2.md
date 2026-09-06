---
tecnologia: NVIDIA Triton Inference Server
categoria: inferencia
url_fonte: https://github.com/triton-inference-server/server
titulo: triton-inference-server/server - The Triton Inference Server provides an optimized cloud and edge inferencing solution
---
Triton Inference Server is an open source inference serving software that streamlines AI inferencing. It enables teams to deploy AI models from multiple deep learning and machine learning frameworks, including TensorRT, PyTorch, ONNX, OpenVINO, Python, RAPIDS FIL, and more. The platform supports inference across cloud, data center, edge and embedded devices on NVIDIA GPUs, x86 and ARM CPU, or AWS Inferentia.

Major capabilities include support for multiple deep learning frameworks and multiple machine learning frameworks. The system features concurrent model execution, allowing multiple models to run simultaneously on the same hardware. Dynamic batching optimizes throughput by grouping requests together. For stateful applications, sequence batching and implicit state management handle models requiring state preservation across requests, which is needed for streaming and conversational workloads where a request depends on prior turns.

The platform supports model composition through model pipelines using ensembling or business logic scripting, enabling complex inference workflows that combine several models with pre- and post-processing steps.

Communication options include HTTP/REST and gRPC inference protocols based on the community developed KServe protocol, alongside a C API and Java API for direct application integration in edge scenarios where a network round trip is undesirable.

Monitoring capabilities provide metrics indicating GPU utilization, server throughput, server latency, and more. The Model Analyzer tool helps optimize model configuration with profiling, so batch size and instance count can be tuned against measured latency and throughput rather than guessed. Users can explicitly manage model availability through loading and unloading functionality.

Extensibility is central to Triton's design. The platform offers a Backend API for custom backends and pre/post processing. Python-based backends enable rapid development without C/C++ compilation. Repository agents add functionality for authentication, decryption, or model conversion during load and unload operations.

Deployment flexibility spans from containerized cloud environments to resource-constrained edge devices via Jetson and JetPack support, with specific guidance for AWS Inferentia integration.
