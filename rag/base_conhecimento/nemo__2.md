---
tecnologia: NVIDIA NeMo
categoria: modelos
url_fonte: https://docs.nvidia.com/nemo-framework/user-guide/latest/overview.html
titulo: Overview - NVIDIA NeMo Framework User Guide
---
NVIDIA NeMo Framework is a scalable and cloud-native generative AI framework built for researchers and developers working on Large Language Models, Multimodal, and Speech AI, including Automatic Speech Recognition and Text-to-Speech. It enables users to efficiently create, customize, and deploy new generative AI models by leveraging existing code and pre-trained model checkpoints.

Developing conversational AI models involves defining, constructing, and training models within particular domains. This process typically requires several iterations to reach a high level of accuracy, fine-tuning on various tasks and domain-specific data, ensuring training performance, and preparing models for inference deployment. NeMo Framework exists to remove the repeated engineering effort in that loop, so teams do not have to rebuild training, customization, and evaluation pipelines from scratch for each new domain or task.

NeMo Framework provides support for the training and customization of Speech AI models. This includes tasks like Automatic Speech Recognition (ASR) and Text-To-Speech (TTS) synthesis. It offers a smooth transition to enterprise-level production deployment with NVIDIA Riva.

Training and customization: NeMo Framework contains everything needed to train and customize speech models, including ASR, Speech Classification, Speaker Recognition, Speaker Diarization, and TTS, in a reproducible manner.

State-of-the-art pre-trained models: NeMo Framework provides state-of-the-art recipes and pre-trained checkpoints of several ASR and TTS models, as well as instructions on how to load them, which shortens the path from an empty project to a working baseline.

Speech tools: NeMo Framework provides tools including NeMo Forced Aligner for generating token-, word-, and segment-level timestamps; Speech Data Processor for simplifying speech data processing; Speech Data Explorer for interactive exploration and analysis of speech datasets; a dataset creation tool for aligning long audio files with transcripts; a comparison tool for ASR models; and an ASR Evaluator for evaluating model performance.

Path to deployment: NeMo models trained or customized using the framework can be optimized and deployed with NVIDIA Riva, which provides containers and Helm charts for push-button deployment.

Programming languages and frameworks: Python serves as the main interface to NeMo Framework, which is built on top of PyTorch.
