---
tecnologia: TensorRT-LLM
categoria: inferencia
url_fonte: https://developer.nvidia.com/tensorrt-llm
titulo: TensorRT LLM | NVIDIA Developer
---
NVIDIA TensorRT LLM is an open-source library designed to deliver high-performance, real-time inference optimization for large language models on NVIDIA GPUs in desktop or data center environments. The library addresses the challenge of maximizing inference performance while minimizing operational costs, enabling developers to serve more concurrent users with faster response times.

The architecture provides a modular Python runtime, PyTorch-native model authoring, and a stable production API specifically customized for NVIDIA platforms. The system features easy-to-use Python APIs, a simple command-line interface, and an extensible framework built on PyTorch foundations, so the same code path used to prototype a model can be carried into production serving.

TensorRT LLM incorporates state-of-the-art optimizations including custom attention kernels, in-flight batching, paged key-value caching, and quantization techniques like FP8 and NVFP4. In-flight batching allows new requests to join a running batch as earlier requests finish, instead of waiting for the whole batch to complete, which raises GPU utilization and lowers time-to-first-token under concurrent load. Additional advanced features encompass speculative decoding methods such as EAGLE-3, multi-token prediction, and various parallelism strategies including wide expert parallelism for mixture-of-experts models.

The v1.0 release is reported to achieve record-setting 8X AI inference performance improvements. Installation options include pip installation or building from source on Linux, with free containers available through NVIDIA NGC for cloud deployment. Pre-configured models include Llama 2, Gemma, Mistral, and Phi-2, all optimized for TensorRT LLM execution.

The ecosystem includes major technology partners such as AWS, Microsoft, Google Cloud, and specialized inference platforms like DeepInfra and Baseten, demonstrating broad industry adoption for production LLM deployment scenarios. TensorRT LLM also works with NVIDIA NIM for model deployment and integrates with NVIDIA Dynamo and the Triton Inference Server for serving.
