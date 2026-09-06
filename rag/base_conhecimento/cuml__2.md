---
tecnologia: cuML
categoria: modelos
url_fonte: https://docs.rapids.ai/api/cuml/stable/
titulo: NVIDIA cuML Documentation
---

NVIDIA cuML e um conjunto de algoritmos de machine learning rapidos e acelerados por GPU, projetados para tarefas de ciencia de dados e analiticas. A plataforma tem como alvo praticantes que querem aproveitar o poder computacional das GPUs sem precisar de conhecimento especializado em programacao de GPU. A filosofia de design se centra em manter compatibilidade com fluxos de trabalho de machine learning existentes: a API do cuML espelha a do scikit-learn, oferecendo o paradigma familiar de fit, predict e transform sem exigir expertise em programacao de GPU.

Os ganhos de desempenho prometidos sao substanciais. A documentacao afirma que o cuML entrega, em media, desempenho de 10 a 50x mais rapido que alternativas baseadas em CPU para cargas de trabalho realistas. Essa aceleracao se aplica a um portfolio diverso, cobrindo mais de 50 algoritmos em todas as principais categorias de machine learning, incluindo clustering, regressao, classificacao, reducao de dimensionalidade e analise de series temporais. A documentacao contextualiza a vantagem observando que, especialmente se os fluxos de trabalho com scikit-learn, umap-learn ou hdbscan levam muitos minutos para completar, o usuario provavelmente se beneficiara do cuML, ja que os estimadores equivalentes do cuML frequentemente rodam em segundos.

Um recurso distintivo atende quem busca aceleracao por GPU sem modificar codigo. A documentacao explica que, com cuml.accel, o cuML tambem pode acelerar automaticamente codigo existente com zero mudancas de codigo. Isso representa um recurso importante de acessibilidade, permitindo que codigo Python de machine learning ja existente se beneficie de aceleracao por GPU por meio de uma camada de aprimoramento transparente.

A plataforma trata requisitos de escalabilidade por meio de capacidades de computacao distribuida. A documentacao menciona suporte abrangente a multi-GPU e multi-node via Dask, permitindo que o cuML escale de estacoes de trabalho unicas ate grandes clusters, sem reestruturacao fundamental de codigo.

O framework aceita formatos diversos de entrada, refletindo a natureza heterogenea dos fluxos modernos de ciencia de dados: funciona com NumPy, cuDF, cuPy e tensores PyTorch. Isso permite integracao com varios ecossistemas populares de computacao cientifica em Python, de arrays NumPy tradicionais a arrays cuPy nativos de GPU e frameworks de deep learning como PyTorch.

Um exemplo pratico de inicio rapido presente na documentacao importa make_blobs de cuml.datasets e DBSCAN de cuml.cluster, gera dados com make_blobs(n_samples=100, centers=3, n_features=2, random_state=42), instancia DBSCAN(eps=1.0, min_samples=5), chama dbscan.fit(X) e imprime dbscan.labels_, ilustrando o paradigma familiar de fit adaptado a cargas aceleradas por GPU.

O suporte de plataforma e limitado a ambientes especificos: o cuML e suportado apenas em sistemas operacionais Linux e no WSL 2. A documentacao direciona os usuarios a pagina de instalacao do RAPIDS para detalhes sobre requisitos de sistema e hardware. O cuML esta disponivel via conda e pip, e a documentacao aponta o RAPIDS Release Selector para orientacao detalhada de instalacao.

Entre as categorias de algoritmos enumeradas estao algoritmos de clustering como DBSCAN, KMeans e AgglomerativeClustering; algoritmos de regressao incluindo LinearRegression e Ridge; algoritmos de classificacao como LogisticRegression e diversos metodos de ensemble; tecnicas de reducao de dimensionalidade como PCA e TSNE; e analise de series temporais com implementacoes de ARIMA e ExponentialSmoothing.

A documentacao enfatiza a posicao do cuML no ecossistema RAPIDS mais amplo: o cuML faz parte do conjunto RAPIDS de bibliotecas open source que permitem pipelines completos de ciencia de dados e analytics inteiramente em GPUs, e funciona de forma integrada com outras bibliotecas RAPIDS como cuDF para manipulacao de dados e cuGraph para analise de grafos.
