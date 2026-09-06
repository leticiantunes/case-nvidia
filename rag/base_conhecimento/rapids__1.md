---
tecnologia: NVIDIA RAPIDS
categoria: dados
url_fonte: https://developer.nvidia.com/topics/ai/data-science/cuda-x-for-data-science
titulo: CUDA-X Data Science Libraries (RAPIDS)
---
CUDA-X e uma colecao de bibliotecas altamente otimizadas e especificas de dominio construidas sobre CUDA, que inclui um conjunto de bibliotecas open source para ciencia de dados acelerada. O ecossistema oferece mais de 100 integracoes com bibliotecas e ferramentas open source do ecossistema de ciencia de dados e APIs de zero-code-change que aceleram ferramentas populares do PyData como pandas e scikit-learn. A proposta de valor central e permitir que cientistas de dados otimizem substancialmente seus fluxos de trabalho existentes sem precisar mudar as ferramentas que ja usam. A partir de 11 de agosto de 2026 a marca RAPIDS passa a fazer parte de NVIDIA CUDA-X, sem mudanca na funcionalidade das bibliotecas.

O problema atacado e o gargalo de desempenho que praticantes de ciencia de dados enfrentam ao processar grandes volumes de dados e executar algoritmos de machine learning complexos em sistemas baseados apenas em CPU. CUDA-X resolve isso usando aceleracao por GPU atraves de primitivas e algoritmos CUDA. As bibliotecas permitem tanto otimizacao em uma unica GPU quanto escalonamento em sistemas distribuidos para operacoes de nivel empresarial.

cuDF e um toolkit com bibliotecas aceleradas por GPU projetadas para otimizar operacoes fundamentais de DataFrame. A pagina reporta desempenho ate 20x mais rapido em Polars e inclui aceleradores drop-in para Polars, pandas e Apache Spark, todos operando sem exigir modificacoes de codigo. A stack cobre implementacoes em Python e C++.

cuML entrega machine learning acelerado por GPU, otimizando algoritmos de aprendizado de maquina para execucao em GPU. A pagina destaca ganhos de ate 50x mais rapido que scikit-learn. A biblioteca inclui aceleradores que funcionam com scikit-learn, UMAP e HDBSCAN, tambem sem exigir mudancas de codigo.

cuGraph e uma biblioteca de analise de grafos acelerada por GPU que otimiza algoritmos de grafos para execucao em GPU, com desempenho ate 48x mais rapido que NetworkX, processando milhoes de nos sem software especializado. O acelerador de zero-code-change para NetworkX permite integracao direta em fluxos de analise de grafos ja existentes.

cuxfilter permite criar visualizacoes interativas com filtragem multidimensional de conjuntos tabulares com mais de 100 milhoes de linhas, adequado para exploracao de dados em larga escala e criacao de dashboards em Python. O ecossistema tambem integra Dask, para escalar pipelines de ciencia de dados acelerados por GPU em multiplos nos, incluindo machine learning, XGBoost e analise de grafos, e o RAPIDS Accelerator for Apache Spark, que acelera fluxos de processamento de dados do Apache Spark em GPU.

As integracoes open source incluem CuPy, Dask, DMLC XGBoost, NetworkX, Polars, PyG, scikit-learn e scverse. As parcerias de plataforma incluem Amazon SageMaker, Anaconda, Azure Machine Learning, Coiled, Databricks, Google Colab, Kaggle e Snowflake.

Casos de uso reais citados na pagina: o banco bunq melhorou a acuracia de deteccao de fraude acelerando o treinamento de modelos em 100x e o processamento de dados em 5x usando NVIDIA cuDF e cuML. A Capital One acelerou seus pipelines de analise financeira e de credito com cuDF e cuML, melhorando o treinamento de modelos em 100x. A Checkout.com acelerou fluxos de analise de dados de minutos para segundos com cuDF. A TGen reduziu o tempo de analise em conjuntos de 4 milhoes de celulas de 10 horas para 3 minutos com RAPIDS-singlecell, construido sobre cuML. O LinkedIn desenvolveu o DARWIN para analise de dados mais rapida sobre cuDF.

A instalacao rapida pode ser feita via conda, com um comando do tipo conda create -n rapids-26.08 -c rapidsai -c conda-forge rapids=26.08 python=3.14 'cuda-version>=13.0,<=13.3', ou via pip usando o indice extra pypi.nvidia.com com pacotes como cudf-cu13, dask-cudf-cu13, cuml-cu13 e cugraph-cu13. Ha guias de implantacao local com conda, pip, Docker e WSL2, em plataformas como Kubernetes, Databricks e Google Colab, e em nuvens como AWS, Azure e GCP.
