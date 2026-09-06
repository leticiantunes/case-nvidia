# NVIDIA Startup AI Radar

Plataforma multi-agente que analisa startups brasileiras a partir de documentos públicos, diagnostica a maturidade técnica em IA de cada empresa e recomenda tecnologias da NVIDIA adequadas ao perfil encontrado.

Projeto desenvolvido para o processo seletivo do Inteli Academy, a partir do TAPI do projeto realizado em parceria com a NVIDIA.

---

## O problema

Grandes laboratórios de IA (OpenAI, Anthropic, Google DeepMind, Meta) deixaram de vender apenas modelos fundacionais e passaram a entregar agentes, buscas, automação e produtos finais. Isso ameaça diretamente startups que se posicionam apenas como *wrappers* de LLM: quem só conecta uma API externa a uma interface, sem dado proprietário, sem workflow profundo e sem otimização técnica, pode ser substituído por uma funcionalidade nativa do próprio laboratório.

Ao mesmo tempo, startups que se tornam *AI-native services* enfrentam problemas concretos conforme escalam: custo de inferência, latência, governança, observabilidade e dependência de fornecedor. É exatamente aí que a stack da NVIDIA resolve.

O problema prático deste projeto: **como a NVIDIA identifica, no meio de centenas de startups brasileiras, quais têm maturidade técnica real em IA e quais têm gargalos que a stack dela resolveria**, para priorizar esforço comercial e do programa NVIDIA Inception.

---

## O que o sistema faz

A partir de uma consulta em linguagem natural, como *"startups de saúde que usam IA no diagnóstico"*, o sistema:

1. converte a pergunta em critérios de busca estruturados;
2. recupera as empresas relevantes de uma base pré-populada com documentos públicos;
3. lê o texto bruto desses documentos e monta um perfil técnico estruturado;
4. classifica a empresa como AI-native, AI-enabled ou non-AI;
5. valida se cada afirmação feita sobre a empresa tem evidência real nos documentos;
6. consulta uma base de conhecimento de tecnologias NVIDIA com busca híbrida e reranking;
7. recomenda tecnologias NVIDIA adequadas aos gargalos identificados;
8. gera um briefing executivo para o time de Startups & VCs.

---

## Arquitetura

O sistema é um grafo do LangGraph. Cada agente é um nó, e todos compartilham um mesmo objeto de estado que atravessa a pipeline inteira.

```
consulta do usuario
   -> Query Planner Agent      converte linguagem natural em filtros de busca
   -> Retriever Agent          recupera empresas e documentos do PostgreSQL
   -> Extractor Agent          transforma texto bruto em perfil estruturado
   -> Startup Classifier       classifica AI-native / AI-enabled / non-AI
   -> Evidence Validator       verifica se cada evidencia existe no documento citado
   -> NVIDIA RAG Agent         busca hibrida na base de tecnologias NVIDIA
   -> Reranker                 reordena os trechos recuperados (Cohere Rerank)
   -> Recommendation Agent     cruza gargalos da startup com tecnologias NVIDIA
   -> Briefing Agent           gera o relatorio executivo final
   -> interface web
```

**Por que grafo e não uma corrente simples de prompts:** o LangGraph mantém estado explícito entre nós, permite transições condicionais (por exemplo, devolver ao Extractor quando o Evidence Validator reprova uma evidência), guarda checkpoints e deixa inspecionar o que cada agente produziu isoladamente. Numa corrente linear de prompts, um erro no meio se propaga silenciosamente até o fim.

---

## Base de dados

A base foi montada manualmente a partir de informações públicas, sem crawler ou scraper, conforme o escopo definido no TAPI.

- **31 startups brasileiras** e **93 documentos** (3 por empresa)
- **16 setores** canônicos, com a descrição original preservada na coluna `setor_detalhado`
- Diversidade proposital de perfis: **13 AI-native, 14 AI-enabled, 4 non-AI**

### Critério de curadoria: fonte acessível para IA

Toda URL candidata foi testada antes de entrar na base: se a página não pudesse ser lida por um agente automatizado (bloqueio 403, `robots.txt` restritivo, SPA em JavaScript que devolve apenas metadados), a fonte era descartada. Cerca de 50 URLs foram reprovadas por esse critério, e uma empresa (Neurotech) foi removida inteira porque todo o domínio bloqueia leitura automatizada.

A decisão é intencional: um sistema cuja conclusão precisa apontar para a fonte que a sustenta não pode depender de fontes que ninguém consegue reabrir para conferir.

### Estrutura

```
startups     id, nome, site, setor, setor_detalhado, estagio,
             localizacao, descricao_curta, ano_fundacao, tamanho_time

documentos   id, startup_id, tipo, titulo, conteudo_texto,
             url_fonte, data_publicacao
```

O campo `ano_fundacao` é texto e não número de propósito: em duas empresas as fontes divergem sobre o ano, e o conflito ficou registrado no próprio campo em vez de ser resolvido por chute.

---

## Stack

| Camada | Escolha | Motivo |
|---|---|---|
| Orquestração | LangGraph | estado explícito, transições condicionais, inspeção por nó |
| LLM dos agentes | Groq, `openai/gpt-oss-120b` | ver "Provedor de LLM" abaixo |
| Banco relacional | PostgreSQL via Docker | dados estruturados das empresas e documentos |
| Banco vetorial | Chroma | roda local, sem serviço externo e sem custo |
| Embeddings | modelo local do Chroma (ONNX) | preserva a cota da Cohere |
| Reranking | Cohere Rerank | recomendado no TAPI para a etapa de reordenação |
| Interface | Streamlit | menor custo de implementação para o peso que tem na entrega |

---

## Decisões técnicas

### Provedor de LLM abstraído

A escolha inicial era rodar os agentes na NVIDIA NIM, por coerência com o tema do projeto. Durante a implementação, dois problemas apareceram:

- dois modelos foram descontinuados em menos de duas semanas, retornando `410 Gone`;
- a chave autenticava na listagem de modelos (`GET /v1/models` retornava 200 com 81 modelos) mas era recusada na inferência (`POST /v1/chat/completions` retornava `403 Authorization failed` em todos eles).

Em vez de ficar refém do fornecedor, o provedor de LLM foi isolado atrás da interface compatível com OpenAI (`ChatOpenAI` com `base_url` configurável). Trocar de provedor passou a custar três variáveis de ambiente, sem alterar nenhum agente. O projeto roda hoje na Groq, e volta para a NVIDIA NIM mudando apenas o `.env`.

### Evidências verificáveis em vez de paráfrase

Cada afirmação produzida pelo Extractor precisa vir acompanhada de um `trecho`: uma citação literal do documento, não um resumo. Isso torna o Evidence Validator um verificador determinístico, que confere se o trecho existe dentro do texto do documento por comparação de string, sem gastar uma chamada de LLM e sem risco de um segundo modelo alucinar ao julgar o primeiro.

A comparação normaliza acentuação, caixa e espaçamento antes de comparar. Sem isso, uma citação legítima seria rejeitada por um acento de diferença, gerando falso negativo justamente no agente responsável pela confiabilidade.

### Palavras-chave ordenam, não filtram

No Retriever, o setor identificado pelo Query Planner funciona como filtro; as palavras-chave apenas pontuam a relevância e definem a ordenação. O motivo é a inconsistência de acentuação entre as fontes: se as palavras-chave filtrassem, um termo acentuado gerado pelo modelo não casaria com o texto sem acento do banco e a busca retornaria vazio sem erro nenhum. Ordenando, um termo que não casa apenas deixa de somar ponto.

### Vocabulário controlado no Query Planner

A lista de setores válidos é injetada dentro do prompt do Query Planner. Sem isso, o modelo devolve categorias que não existem na base (por exemplo, "saúde" no lugar de "healthtech"), o Retriever não encontra nada e a falha é silenciosa.

---

## Como rodar

Pré-requisitos: Python 3.11+, Docker Desktop e uma chave de API de um provedor compatível com OpenAI.

```bash
# 1. ambiente
python -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
pip install -r requirements.txt

# 2. variaveis de ambiente
cp .env.example .env
# preencha LLM_API_KEY e COHERE_API_KEY

# 3. banco de dados
docker compose up -d
python data/load_csv.py            # cria as tabelas e carrega 31 startups e 93 documentos

# 4. pipeline
python agents/pipeline.py
```

---

## Estrutura do repositório

```
agents/     nos do grafo LangGraph
rag/        ingestao e consulta da base de conhecimento NVIDIA
app/        interface web
data/       base de startups, schema e script de carga
docs/       documentacao de apoio
```

---

## Status dos entregáveis

| Entregável | Status |
|---|---|
| Sistema multi-agente com LangGraph | Query Planner, Retriever e Extractor implementados |
| RAG NVIDIA com reranking | em desenvolvimento |
| Motor de recomendação | em desenvolvimento |
| Interface web | em desenvolvimento |
| Diferencial do projeto | ver abaixo |

---

## Diferencial do projeto

> PREENCHER: escolha o que você quer defender como diferencial. Dois candidatos já
> existem e estão documentados acima:
>
> 1. o critério de curadoria por acessibilidade para IA, que é uma decisão de
>    arquitetura de dados pouco comum e que sustenta a rastreabilidade do sistema;
> 2. a medição de acurácia do classificador contra a hipótese de perfil registrada
>    em `docs/perfil_hipotese.md`, que transforma "o agente funciona" em um número.
>
> Escreva aqui em uma ou duas frases qual deles você escolheu e por quê.

---

## Observações

O uso de IA como ferramenta de desenvolvimento é permitido e esperado neste projeto. As decisões de arquitetura registradas neste README foram tomadas ao longo da implementação, a partir dos problemas que apareceram na prática, e estão detalhadas em `docs/decisoes.md`.
