---
tecnologia: cuDF
categoria: dados
url_fonte: https://developer.nvidia.com/blog/rapids-cudf-accelerates-pandas-nearly-150x-with-zero-code-changes
titulo: RAPIDS cuDF Accelerates pandas Nearly 150x with Zero Code Changes
---

pandas e a principal biblioteca de DataFrame do ecossistema Python de ciencia de dados, valorizada por sua API intuitiva e por suas capacidades. No entanto, pandas encontra limitacoes significativas de desempenho quando os conjuntos de dados chegam a faixa de gigabytes em sistemas apenas com CPU. A arquitetura tradicional do pandas depende de processamento single-threaded em CPU, o que se torna cada vez mais um gargalo com volumes maiores de dados.

Na GTC 2024 a NVIDIA anunciou que o cuDF passa a levar aceleracao por GPU a 9,5 milhoes de usuarios de pandas sem exigir nenhuma mudanca de codigo. Historicamente, o cuDF exigia que desenvolvedores reescrevessem codigo especificamente para execucao em GPU, abandonando a API pandas no processo. A nova abordagem muda esse paradigma ao fornecer o que os desenvolvedores chamam de uma experiencia unificada de CPU e GPU.

Em vez de forcar a escolha entre pandas e aceleracao por GPU, a implementacao atualizada do cuDF gerencia ambos os recursos computacionais simultaneamente. As operacoes rodam na GPU se possivel e na CPU, usando pandas, caso contrario, com a biblioteca sincronizando entre GPU e CPU nos bastidores conforme necessario. Essa abordagem hibrida garante que funcionalidades nao suportadas continuem funcionando.

Para ativar a aceleracao por GPU em notebooks Jupyter, o desenvolvedor precisa apenas carregar a extensao do cuDF com duas linhas: %load_ext cudf.pandas seguido de import pandas as pd. Para scripts Python executados fora de notebooks, a invocacao e igualmente simples: python -m cudf.pandas script.py. Esse caminho de adocao sem atrito significa que bases de codigo pandas existentes exigem zero modificacoes para se beneficiar da aceleracao por GPU. A documentacao enfatiza a aceleracao com zero mudancas de codigo: basta carregar a extensao do cuDF no Jupyter Notebook ou usar a opcao de modulo Python do cuDF.

Uma consideracao critica no mundo real e o ecossistema de ferramentas e bibliotecas construidas em torno do pandas. O modo acelerador de pandas e compativel com a maioria das bibliotecas de terceiros que operam sobre objetos pandas, e chega a acelerar operacoes pandas dentro dessas bibliotecas. Isso estende o alcance da aceleracao por GPU alem do uso direto de pandas: quando cientistas de dados empregam scikit-learn, plotly ou outras bibliotecas que aceitam objetos pandas, essas bibliotecas se beneficiam de operacoes aceleradas por GPU executando por baixo.

Para validar essas afirmacoes, a NVIDIA fez benchmark do cuDF usando o DuckDB Database-like Ops Benchmark, originalmente desenvolvido pela H2O.ai. Esse benchmark implementa uma serie de tarefas analiticas comuns, como juntar dados ou computar medidas estatisticas por grupo. O conjunto de teste tinha 5 gigabytes de dados. O pandas tradicional exigia minutos para executar a serie de operacoes de join e de group by avancado. Em contraste, o mesmo codigo pandas nao modificado executado atraves da interface unificada CPU/GPU do cuDF terminou em apenas 1 ou 2 segundos, o que representa uma melhoria de desempenho de aproximadamente 150 vezes.

O benchmark foi executado em hardware NVIDIA Grace Hopper com processadores Intel Xeon Platinum 8480C, rodando pandas v2.2 e RAPIDS cuDF 23.10. A experiencia unificada CPU/GPU do cuDF transforma minutos de processamento em apenas 1 ou 2 segundos sem exigir mudanca de codigo. Vale notar que atingir essa vantagem envolveu usar a GPU para a maior parte das operacoes e a CPU para uma pequena parcela, para garantir que o fluxo de trabalho fosse bem-sucedido, demonstrando como o mecanismo automatico de fallback trata casos de borda mantendo o desempenho geral.

O recurso passou de beta para disponibilidade geral com o release RAPIDS v24.02, anunciado na GTC 2024, e o suporte pelo NVIDIA AI Enterprise 5.0 foi previsto para a primavera seguinte. A NVIDIA disponibiliza um notebook de walkthrough detalhado em ambiente gratuito com GPU no Google Colab.
