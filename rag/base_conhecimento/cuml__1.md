---
tecnologia: cuML
categoria: modelos
url_fonte: https://developer.nvidia.com/topics/ai/data-science/cuda-x-data-science-libraries/cuml
titulo: NVIDIA cuML - GPU-Accelerated Machine Learning
---

NVIDIA cuML e uma biblioteca open source CUDA-X que acelera scikit-learn, UMAP e HDBSCAN em GPUs, sem exigir mudancas de codigo. A biblioteca nasceu no ecossistema RAPIDS, que passa a integrar a marca CUDA-X a partir de 11 de agosto de 2026, sem alteracao de funcionalidade. A missao central do cuML e otimizar operacoes fundamentais de machine learning para execucao em GPU, o que acelera significativamente o desenvolvimento e o treinamento de modelos, com iteracoes mais rapidas de teste e ajuste de parametros.

O modulo cuml.accel entrega a aceleracao com zero mudancas de codigo: e possivel rodar codigo existente de scikit-learn, UMAP ou HDBSCAN em GPUs sem modificacoes. Isso e feito por um mecanismo de intercepcao transparente, no qual o cuML atua como proxy entre o codigo do usuario e as implementacoes subjacentes. Quando o modulo cuml.accel e carregado, ele intercepta os estimadores das bibliotecas baseadas em CPU e decide dinamicamente se executa a operacao em GPU ou em CPU, conforme a cobertura e a disponibilidade do algoritmo.

O mecanismo de fallback garante robustez: se uma implementacao acelerada por GPU nao cobrir determinada operacao, o cuML roteia automaticamente para execucao em CPU. Da mesma forma, se um modelo for treinado em GPU mas precisar de um metodo nao suportado na versao GPU, o cuML reconstroi o modelo treinado na CPU e usa a versao do scikit-learn.

Ha tres formas de habilitar a aceleracao apos a instalacao. Em ambientes IPython e Jupyter usa-se o comando magico %load_ext cuml.accel seguido de import sklearn. Para scripts Python, a invocacao por linha de comando e python -m cuml.accel script.py. Quando flags de linha de comando nao sao viaveis, e possivel usar o metodo explicito: import cuml.accel, cuml.accel.install() e depois import sklearn. A documentacao observa que nem todos os estimadores do cuML sao suportados no cuml.accel hoje, que esta em open beta, e que as limitacoes conhecidas estao detalhadas nos recursos oficiais.

Quanto a desempenho, a pagina reporta scikit-learn ate 50x mais rapido, com o speedup medido como desempenho medio de treinamento de algoritmos tradicionais de machine learning rodando com cuml.accel e codigo scikit-learn em GPU versus scikit-learn em CPU. A configuracao de benchmark foi NVIDIA cuML 25.02 em NVIDIA H100 80GB HBM3 contra scikit-learn v1.5.2 em Intel Xeon Platinum 8480CL. Para reducao de dimensionalidade e clustering, a aceleracao chega a 60x mais rapido em UMAP e 175x mais rapido em HDBSCAN, com as mesmas especificacoes, comparando cuML 25.02 em H100 80GB HBM3 contra umap-learn v0.5.7 e hdbscan v0.8.40 em Intel Xeon Platinum 8480CL.

Sobre escalabilidade, o cuML utiliza eficientemente sistemas de GPU unica para processar conjuntos de dados que sobrecarregam implementacoes baseadas em CPU. A capacidade distribuida vai alem: o cuML acelera aplicacoes de machine learning distribuidas em escala, com exemplos reais de ate 6 TB de dados em clusters multi-node multi-GPU via a popular API Apache Spark MLlib.

Entre os casos de uso documentados estao otimizacao de portfolio, com um starter kit que demonstra um fluxo ponta a ponta de machine learning e otimizacao usando cuML para ajuste e amostragem de KDE; analise de genomica de celula unica em escala; modelagem de topicos com melhoria de desempenho pela reducao de clusters de ruido; previsao de series temporais com skforecast, permitindo trabalhar com conjuntos e janelas de previsao maiores; e um caso de primeiro lugar em competicao Kaggle usando stacking com cuML, treinando e combinando eficientemente numerosos modelos diversos.

Para instalacao via conda, o comando indicado cria um ambiente com cuml=26.08, python=3.14 e cuda-version>=13.0,<=13.3 a partir dos canais rapidsai e conda-forge. Via pip, usa-se pip install "cuml-cu13==26.8.*". Um seletor de instalacao oferece opcoes adicionais para Docker, WSL2 e instalacao de bibliotecas individuais.
