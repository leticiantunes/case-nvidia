# Roteiro do vídeo (máximo 7 minutos)

Não decore. Este roteiro define **o que mostrar na tela e em que ordem**. As frases
você diz com suas palavras, senão soa lido e a banca percebe.

Grave a tela com o navegador e o terminal já abertos e posicionados. Deixe o
`dashboard.py` rodando antes de começar a gravar.

---

## 0:00 a 0:45: o problema

**Tela:** slide simples ou o README aberto.

O que dizer:

- Laboratórios de IA passaram a entregar produto final, não só modelo. Isso ameaça
  startups que são só wrapper de LLM.
- A NVIDIA precisa achar, no meio de centenas de startups brasileiras, quais têm
  maturidade técnica real e quais têm gargalo que a stack dela resolve.
- Quem usa o sistema é o gerente de Startups & VCs, que precisa decidir onde gastar tempo.
- Dê nome ao sistema logo no início ("o sistema que eu construí, o Nivra, faz X"),
  porque é o nome que aparece na tela do dashboard depois.

Não gaste mais que 45 segundos aqui. A banca conhece o problema, escreveu ele.

---

## 0:45 a 1:30: arquitetura

**Tela:** o diagrama do grafo no README, ou o `pipeline.py` mostrando os `add_node`.

O que dizer:

- Oito agentes como nós de um grafo LangGraph, com estado compartilhado.
- **Por que grafo e não corrente de prompts:** estado explícito entre nós, transição
  condicional possível, e dá para inspecionar o que cada agente produziu isoladamente.
  Numa corrente linear, erro no meio se propaga em silêncio.
- **Aponte a ordem:** o validador roda ANTES do classificador. O classificador só
  raciocina sobre evidência já verificada. Se fosse ao contrário, uma alucinação do
  extrator viraria classificação errada com aparência de fundamentada.

---

## 1:30 a 3:30: demonstração ao vivo (o pedaço mais importante)

**Tela:** terminal e depois o dashboard.

"Projeto que não executa" é critério eliminatório, então **mostre rodando de verdade**.

1. Rode `python agents/pipeline.py` com `LIMITE_STARTUPS = 2`. Enquanto roda, narre
   os prints aparecendo: planner encontrou o setor, retriever trouxe as empresas,
   extractor montou o perfil, validador aprovou X de Y evidências, classificador
   decidiu, RAG recuperou as tecnologias, recomendação saiu.
2. Abra o dashboard. Mostre uma empresa AI-native aberta: justificativa, sinais a
   favor e contra, recomendação com prioridade e próxima ação, e o link da fonte.
3. **Abra a aba Qualidade.** Mostre uma empresa com taxa de validação baixa e diga
   que o sistema rejeitou aquelas evidências porque o trecho não existia no documento.
4. Abra a aba Briefing.

Se a cota estiver esgotada na hora de gravar, rode com o resultado já salvo e diga
que o processamento foi feito previamente. Não improvise com erro na tela.

---

## 3:30 a 5:30: decisões técnicas

Escolha **quatro** destas. São todas reais e todas suas.

**1. Curadoria com critério de acessibilidade para IA**
Toda URL foi testada antes de entrar na base. Cerca de 50 foram reprovadas por
bloqueio, e uma empresa inteira (Neurotech) saiu porque o domínio devolve 403.
Motivo: um sistema cuja conclusão aponta para a fonte não pode depender de fonte
que ninguém consegue reabrir.

**2. Provedor de LLM abstraído**
A escolha inicial era NVIDIA NIM. Dois modelos foram descontinuados em duas semanas,
e a chave autenticava na listagem mas era recusada na inferência com 403. Em vez de
ficar refém, isolei o provedor atrás da interface compatível com OpenAI. Trocar de
provedor virou três linhas de `.env`, sem tocar em nenhum agente.

**3. Evidência verificável e validador determinístico**
Cada afirmação carrega um trecho literal do documento. O validador confere se aquele
trecho existe, comparando texto normalizado, sem gastar chamada de LLM. A alternativa
óbvia, pedir para outro modelo julgar, custaria cota e poderia alucinar ao avaliar.
Mostre o caso da URL inventada que o validador pegou.

**4. Bug de idioma no RAG, com número**
A base tem 26 documentos em inglês e 7 em português, e o embedding padrão do Chroma
é monolíngue. Consulta em português caía nos documentos errados: 2 de 3 consultas de
teste falhavam. Mitiguei com busca bilíngue e pool maior, deixando o reranking da
Cohere, que é multilíngue, ordenar. Resultado: 3 de 3, com o score do topo subindo de
0,47 para 0,75 e de 0,42 para 0,80. A correção definitiva seria trocar o embedding
por um multilíngue, o que exigiria reindexar; ficou documentado como melhoria.

**5. Fusão por Reciprocal Rank Fusion**
Similaridade de cosseno e score BM25 vivem em escalas diferentes e não são somáveis.
O RRF olha só a posição em cada lista, então dispensa normalização.

**6. Projeto dentro de um orçamento de cota**
Medi o consumo por agente: cerca de 6.600 tokens por empresa, o que dá 205 mil para
as 31, praticamente o limite diário do tier gratuito. Por isso existem pausa entre
chamadas, retry com espera exponencial, tolerância a falha por empresa e resultado
persistido em disco. Nenhuma dessas escolhas é enfeite.

---

## 5:30 a 6:30: qualidade e diferencial

**Tela:** saída do `medir_acuracia.py`.

- Antes de o classificador existir, registrei uma hipótese de perfil para as 31
  empresas em `docs/perfil_hipotese.md`.
- Mostre a acurácia, a matriz de confusão e **o acerto por nível de confiança**.
- Se o agente acertar mais quando declara confiança alta, diga o nome disso: calibração.
  Ele sabe quando não sabe.
- **Seja honesta com o número.** Se der 60%, diga 60% e explique onde divergiu e por quê.
  Um projeto que mede e reporta vale mais que um que afirma funcionar sem medir.
- Cite um caso de divergência concreto e o que ele revelou.

---

## 6:30 a 7:00: fecho

- O que ficou de fora e por quê (embedding multilíngue, rodar as 31 com o modelo maior).
- Uma frase sobre o que você faria com mais uma semana.

Não agradeça por 20 segundos. Termine no conteúdo.

---

## Checklist antes de apertar o gravar

- [ ] `.env` fora da tela (não exponha chave de API em vídeo)
- [ ] terminal com fonte grande, dá para ler no vídeo
- [ ] dashboard já aberto e carregado
- [ ] `data/resultado_completo.json` existe
- [ ] cronômetro à vista, 7 minutos é o teto
- [ ] teste de áudio de 20 segundos antes de gravar tudo
