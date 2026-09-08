# Decisões técnicas

Registro das decisões tomadas durante o desenvolvimento, com o problema que as
originou e a consequência de cada uma. Quase todas nasceram de um obstáculo real
encontrado na implementação, não de escolha feita no papel antes de começar.

---

## 1. Curadoria da base com critério de acessibilidade para IA

**Problema.** O sistema precisa apontar a fonte de toda conclusão que produz. Fonte
que um agente automatizado não consegue reabrir quebra essa garantia.

**Decisão.** Toda URL candidata foi testada antes de entrar na base. Se a página não
pudesse ser lida por um agente (bloqueio 403, `robots.txt` restritivo, página em
JavaScript que devolve apenas metadados), a fonte era descartada e substituída.

**Consequência.** Cerca de 50 URLs reprovadas. Uma empresa inteira, a Neurotech, saiu
da base porque todo o domínio bloqueia leitura automatizada; foi substituída pela
Justos. A base final tem 31 empresas e 93 documentos, todos verificáveis.

---

## 2. Estrutura de dados que preserva o conflito entre fontes

**Problema.** Em duas empresas, fontes diferentes divergem sobre o ano de fundação.

**Decisão.** O campo `ano_fundacao` é texto e não número, e o conflito fica registrado
dentro do próprio campo.

**Consequência.** A carga no Postgres não quebra, e a incerteza fica visível em vez de
ser resolvida por um chute que ninguém conseguiria auditar depois.

---

## 3. Normalização do campo setor

**Problema.** A base tinha 28 setores diferentes para 31 empresas, praticamente uma
categoria por empresa. Nenhum filtro funcionaria em cima disso.

**Decisão.** Reduzi para 16 setores canônicos e preservei a descrição original numa
coluna nova, `setor_detalhado`.

**Consequência.** O Query Planner passou a ter um vocabulário fechado para escolher, e
o Retriever passou a filtrar de verdade. Nenhuma informação foi perdida.

---

## 4. Provedor de LLM abstraído atrás de interface compatível com OpenAI

**Problema.** A escolha inicial era rodar os agentes na NVIDIA NIM, por coerência com o
tema. Dois modelos foram descontinuados em menos de duas semanas, retornando `410`. E a
chave autenticava na listagem de modelos (`GET /v1/models` devolvia 200 com 81 modelos)
mas era recusada na inferência, com `403 Authorization failed` em todos eles.

**Decisão.** Isolei o provedor atrás de `ChatOpenAI` com `base_url` configurável, em vez
de usar a classe específica da NVIDIA.

**Consequência.** Trocar de provedor passou a custar três variáveis de ambiente, sem
tocar em nenhum agente. O projeto roda hoje na Groq e volta para a NVIDIA NIM mudando
apenas o `.env`.

---

## 5. Evidência com trecho literal, e validador determinístico

**Problema.** A primeira versão do Extractor produzia afirmações cuja "evidência" era a
própria conclusão reescrita. Não dava para verificar nada.

**Decisão.** Cada evidência passou a exigir um campo `trecho`, com citação literal do
documento, separada da `afirmacao`. O Evidence Validator confere se aquele trecho existe
dentro do texto do documento, comparando strings normalizadas em caixa, acentuação e
espaçamento. **Sem usar LLM.**

**Consequência.** O validador não gasta cota, é reproduzível, e não corre o risco de um
segundo modelo alucinar ao julgar o primeiro. Ele detectou casos reais: trechos que não
existiam nos documentos e, num deles, uma URL inventada pelo modelo (`ia-saude-capta` no
lugar de `isa-saude-capta`).

A normalização antes de comparar não é detalhe: sem ela, uma citação legítima seria
rejeitada por um acento de diferença, gerando falso negativo justamente no agente
responsável pela confiabilidade.

---

## 6. Validação de citação com reticências, por fragmentos

**Problema.** Exigir citação byte a byte de um modelo generativo é frágil. Em algumas
execuções o modelo citava com reticências, e evidências legítimas eram rejeitadas.

**Decisão.** O validador separa a citação nos pontos de reticência e confere cada
fragmento com pelo menos 25 caracteres. Fragmento curto é ignorado, porque casaria por
acaso em qualquer texto.

**Consequência.** A rigidez saiu do formato e ficou onde importa: a verificação de que
cada pedaço citado existe na fonte. A garantia não foi afrouxada, o critério foi corrigido.

---

## 7. Ordem dos agentes: validador antes do classificador

**Decisão.** O Evidence Validator roda antes do Startup Classifier, e o classificador
recebe o perfil **sem** o campo de evidências rejeitadas.

**Motivo.** Se fosse o contrário, uma alucinação do Extractor viraria uma classificação
errada com aparência de fundamentada. Numa versão anterior o classificador recebia o
perfil inteiro, incluindo as evidências reprovadas, e chegou a listar sete sinais a favor
para uma empresa cujas evidências tinham sido todas rejeitadas.

---

## 8. Busca híbrida com fusão por Reciprocal Rank Fusion

**Problema.** Busca vetorial sozinha não acerta nome de produto ("cuDF" é token raro para
o embedding). Busca lexical sozinha não entende "meu modelo está lento" sem a palavra
"latência".

**Decisão.** As duas buscas rodam em paralelo e as listas são fundidas por RRF, não pela
soma dos scores.

**Motivo.** Similaridade de cosseno e score BM25 vivem em escalas diferentes e não são
comparáveis. O RRF olha apenas a posição de cada resultado em cada lista, o que dispensa
normalização.

---

## 9. Busca bilíngue no RAG (bug de idioma)

**Problema.** Duas de três consultas de teste retornavam o documento errado. Causa raiz:
a base tem 26 documentos em inglês e 7 em português, e o embedding padrão do Chroma
(`all-MiniLM-L6-v2`) é treinado apenas em inglês. Consulta em português ficava mais
próxima dos poucos trechos em português do que dos trechos em inglês que respondiam a
pergunta.

**Decisão.** A função de busca passou a aceitar também a consulta em inglês. As duas
versões alimentam busca vetorial e BM25, as quatro listas são fundidas por RRF, e o
reranking final usa a consulta em português, porque o modelo da Cohere é multilíngue.
O agente de RAG gera a consulta de busca em inglês por padrão.

**Resultado medido:**

| Consulta | Antes | Depois |
|---|---|---|
| custo e latência de inferência | API Catalog (0,474), errado | **Triton (0,750)**, TensorRT-LLM, NIM |
| dados tabulares | RAPIDS (0,833) | RAPIDS (0,834) |
| controlar agente de IA | conceito AI-native (0,424), errado | **NeMo Guardrails (0,800)** |

De 1 acerto em 3 para 3 em 3.

**O que ficou de fora.** A correção definitiva seria trocar o embedding por um modelo
multilíngue (`paraphrase-multilingual-MiniLM-L12-v2`), o que exigiria instalar
`sentence-transformers` e reindexar a base. Não coube no prazo e está documentado na
docstring da função `buscar`.

---

## 10. Embeddings locais, Cohere reservada ao reranking

**Problema.** A chave trial da Cohere tem teto de 1.000 chamadas por mês. Gerar embeddings
de todos os chunks consumiria boa parte disso.

**Decisão.** Os embeddings são gerados pelo modelo local do Chroma (ONNX, já incluso na
biblioteca) e a Cohere é usada exclusivamente no reranking, que é chamado uma vez por
consulta e não uma vez por chunk.

**Consequência.** Custo zero de API na ingestão, e a cota da Cohere dura até a entrega.

---

## 11. Tratamento de erro que distingue falha transitória de determinística

**Problema.** Três falhas diferentes apareciam com o mesmo sintoma, "não veio JSON":
resposta em prosa (prompt sem instrução de formato), resposta vazia (orçamento consumido
no raciocínio interno do modelo) e JSON cortado no meio (teto de tokens insuficiente).

**Decisão.** O retry cobre apenas falha de rede, erro 429 e resposta vazia, que são
transitórias. Resposta malformada **não** é repetida, porque o problema está no prompt e
repetir só gastaria cota. Além disso, uma função desembrulha o `RetryError` do tenacity
para mostrar a causa real.

**Consequência.** O `RetryError` sozinho é inútil para diagnóstico: pode ser limite de
taxa, chave inválida, parâmetro rejeitado ou timeout, e todos apareciam iguais.
Tratamento de erro que engole a causa é pior que não ter tratamento, porque dá aparência
de robustez enquanto esconde o diagnóstico.

Também foi necessário reduzir o `reasoning_effort` para `low`: os modelos da família
gpt-oss gastam tokens de raciocínio que contam dentro do teto da resposta, e extração
estruturada é tarefa de leitura e formatação, não de raciocínio profundo.

---

## 12. Projeto dentro de um orçamento de cota

**Problema.** O tier gratuito do Groq tem teto de 200 mil tokens por dia por modelo.
Medindo o consumo por agente: cerca de 2.100 tokens no Extractor, 1.200 no Classifier,
800 na consulta do RAG e 2.500 no Recommendation, o que dá **~6.600 tokens por empresa**.
Para 31 empresas, cerca de 205 mil, praticamente o limite diário inteiro.

**Decisão.** Uma rodada completa passou a ser tratada como evento planejado, não como
comando casual. O sistema tem pausa entre chamadas, retry com espera exponencial,
tolerância a falha por empresa e resultado persistido em disco.

**Consequência.** A classificação rodou nas 31 empresas. O processamento completo, com
RAG, recomendação e briefing, foi demonstrado sobre um recorte de 10, por decisão de
custo e não por limitação do sistema.

---

## 13. Processamento em lote retomável

**Problema.** A rodada de 10 empresas com RAG levou 8 minutos e só gravava no final.
Quando a cota estourou na sétima, o trabalho das seis anteriores existia apenas na
memória do processo.

**Decisão.** O script `scripts/completar.py` trabalha em cima do JSON já salvo, refaz
somente as empresas que falharam por erro técnico, e grava a cada empresa concluída.
Ele distingue falha técnica (refaz) de recusa consciente do agente (não refaz).

**Consequência.** A execução virou incremental: rodar de novo continua de onde parou,
em vez de recomeçar.

---

## 14. Interface consome resultado salvo, não executa a pipeline

**Decisão.** O dashboard lê `data/resultado_completo.json` em vez de rodar os agentes ao vivo.

**Motivo.** Processar as empresas leva minutos e consome cota. A pipeline é o que produz;
a interface é o que apresenta. Separar as duas responsabilidades também torna a
demonstração previsível, sem depender de disponibilidade de API no momento da apresentação.

---

## 15. Medição de qualidade contra hipótese registrada previamente

**Decisão.** Antes de o classificador existir, registrei em `docs/perfil_hipotese.md` uma
hipótese de perfil para as 31 empresas, lida dos mesmos documentos. Depois comparei a
saída do agente com essa hipótese.

**Resultado.** 17 de 31, ou 55% de concordância.

**Leitura honesta do número, que importa mais que o número:**

- Parte dos erros vem da extração, não da classificação. A Hand Talk, cujo produto é
  tradução automática para Libras, foi classificada como non-AI porque só 2 de 7
  evidências foram validadas. A Agrosmart teve 0 evidências extraídas.
- O acerto na categoria non-AI (4 de 4) está **inflado**: Méliuz, Buser e QuintoAndar
  tiveram 0 evidências extraídas, e perfil vazio cai em non-AI por padrão. O sistema
  acertou pelo motivo errado.
- A calibração está fraca: confiança alta acertou 56% e confiança baixa acertou 67%,
  ou seja, invertida, provavelmente pelo mesmo efeito dos perfis vazios.

**Conclusão.** O gargalo de qualidade do pipeline está na extração, não na classificação.
Esse é o ponto onde eu investiria primeiro se tivesse mais tempo.
