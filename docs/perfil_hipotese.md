# Hipótese de perfil das startups da base

**Atenção: este arquivo NÃO deve ser usado como entrada da pipeline.**

Ele existe para um único propósito: servir de referência para você avaliar depois se o seu Startup Classifier Agent está classificando bem. A classificação oficial de cada empresa precisa ser produzida pelo agente, a partir das evidências dos documentos, e não copiada daqui.

Estas hipóteses vieram da leitura das fontes durante a curadoria (setembro de 2026). Elas são discutíveis de propósito: várias empresas ficam na fronteira entre categorias, e é justamente isso que dá trabalho interessante ao classificador.

| id | empresa | hipótese | por quê |
|---|---|---|---|
| startup-01 | Traive | AI-native | IA proprietária avalia 2.500+ pontos de dados; sem o modelo não há produto |
| startup-02 | Nagro | AI-enabled | crédito rural regulado com pilares clássicos de bureau; IA aparece como investimento anunciado |
| startup-03 | Datarisk (WeCogno) | AI-native | plataforma de MLOps e Model as a Service; o produto é o modelo |
| startup-04 | Agrosmart | AI-enabled | sensores, satélite e irrigação; analytics é central, IA como núcleo não se sustenta nas fontes |
| startup-05 | Justos | AI-native | precificação por telemetria; CEO afirma ser "empresa de IA que vende seguros" |
| startup-06 | Cortex Intelligence | AI-native | "Augmented Intelligence for Go-to-Market", ML sobre big data como mecanismo do produto |
| startup-07 | Arvo | AI-native | a própria plataforma de IA audita contas médicas |
| startup-08 | Isa Saúde | AI-enabled | operação assistencial domiciliar; IA é camada de apoio preditivo |
| startup-09 | Portal Telemedicina | AI-enabled | core é telediagnóstico com médicos; IA faz triagem e checagem cruzada |
| startup-10 | Laura | AI-native | motor preditivo lê prontuários e antecipa sepse; é o produto |
| startup-11 | Jusbrasil | AI-enabled | nasceu como base de dados jurídicos; IA generativa é camada de 2025 |
| startup-12 | Blip | AI-enabled | nasceu em 1999 como mensageria; IA é camada sobre plataforma de canais |
| startup-13 | Weni | AI-native | modelos de NLP próprios são o núcleo dos repositórios |
| startup-14 | Tako | AI-native | fundada em torno de agentes de IA para o ciclo de RH |
| startup-15 | Gupy | AI-native (discutível) | afirma ter a "primeira IA para R&S do Brasil", mas cresceu por aquisições não AI-first |
| startup-16 | Hand Talk | AI-native | tradução automática para Libras com avatar 3D é o produto |
| startup-17 | Cobli | AI-enabled | núcleo é hardware IoT e telemetria; IA identifica fadiga e distração |
| startup-18 | Logcomex | AI-enabled | nasceu de big data e tracking; agentes de IA são camada recente |
| startup-19 | Looqbox | AI-native | consulta em linguagem natural é o produto desde 2013 |
| startup-20 | Semantix | AI-native | deep tech de dados e IA com arquitetura proprietária |
| startup-21 | Aquarela | AI-native | vende IA como produto, com metodologia e plataforma próprias |
| startup-22 | Contabilizei | AI-enabled | contabilidade digital; IA aparece como apoio ao atendimento |
| startup-23 | Olist | AI-enabled | ERP e logística; marca se diz "AI First" mas a operação é integração |
| startup-24 | Nuvemshop | AI-enabled | SaaS de lojas virtuais; IA (Lumi) é funcionalidade no painel |
| startup-25 | Méliuz | non-AI | nenhuma fonte lida menciona IA; cashback e serviços financeiros |
| startup-26 | Zenvia | AI-enabled | base de receita é CPaaS/SMS; posicionamento novo é agentes de IA |
| startup-27 | Buser | non-AI | nenhuma menção a IA nas 3 fontes; intermediação de fretamento |
| startup-28 | QuintoAndar | non-AI | zero menções a IA; fluxo digital e garantia financeira |
| startup-29 | Hotmart | AI-enabled | checkout e afiliados; "Tutor com IA" é funcionalidade agregada |
| startup-30 | Loggi | AI-enabled | IA roteiriza pacotes, mas o que se vende é frete e malha logística |
| startup-31 | Cuponeria | non-AI | nenhuma menção a IA; produto transacional |

## Distribuição

- AI-native: 13
- AI-enabled: 14
- non-AI: 4

## Como usar isso a seu favor

Depois que o Startup Classifier Agent estiver rodando, compare a saída dele com esta tabela e calcule quantas ele acertou. Isso vira material forte para o vídeo: mostrar que você mediu a qualidade do classificador em vez de só afirmar que ele funciona. Onde ele discordar, leia a justificativa dele: se a evidência que ele citou for boa, quem estava errada era a hipótese, não o agente.

Casos de fronteira que valem atenção especial na avaliação: Gupy, Zenvia, Olist e Logcomex, todas empresas cujo marketing se posiciona como IA mas cuja operação histórica é outra. Um bom classificador deveria perceber essa diferença a partir dos documentos.
