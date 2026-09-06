---
tecnologia: TensorRT-LLM
categoria: inferencia
url_fonte: https://github.com/NVIDIA/TensorRT-LLM
titulo: NVIDIA/TensorRT-LLM - Easy-to-use Python API to define LLMs with state-of-the-art inference optimizations on NVIDIA GPUs
---
TensorRT LLM is an open-sourced library for optimizing LLM and Visual Gen inference. It provides state-of-the-art optimizations, including custom kernels for common inference operations such as attention, GEMMs, and MoE, and algorithmic runtime optimizations such as Prefill-Decode disaggregation, Wide Expert Parallelism, and Speculative Decoding, to perform inference efficiently on NVIDIA GPUs.

Architected on PyTorch, TensorRT LLM provides a high-level Python LLM API that supports a wide range of inference setups, from single-GPU to multi-GPU or multi-node deployments. It includes built-in support for various parallelism strategies and advanced features. The LLM API integrates seamlessly with the broader inference ecosystem, including NVIDIA Dynamo and the Triton Inference Server, so an optimized engine can be placed directly behind a production serving layer.

TensorRT LLM is designed to be modular and easy to modify. Its PyTorch-native architecture allows developers to experiment with the runtime or extend functionality. Several popular models are also pre-defined and can be customized using native PyTorch code, making it easy to adapt the system to specific needs without leaving the framework the model was authored in.

TensorRT LLM also contains components to create Python and C++ runtimes that orchestrate the inference execution in a performant way. The library supports quantization techniques including FP8, FP4, and INT4 AWQ, paged KV cache management, and various parallelism strategies including tensor parallelism and pipeline parallelism. Quantization reduces the memory footprint and bandwidth cost of weights and activations, while paged KV cache management avoids the memory fragmentation that otherwise limits how many concurrent sequences a GPU can hold.

Reported benchmark results include Llama 3.3 70B inference throughput increased 3x with NVIDIA TensorRT-LLM speculative decoding, 24,000 tokens per second for Meta Llama 3 inference, and multiblock attention boosting throughput by more than 3x for long sequence lengths. TensorRT LLM supports NVIDIA's latest accelerators including the Blackwell and Hopper architectures, with documented results on NVIDIA Blackwell for DeepSeek-R1 inference performance and on H200 platforms.
