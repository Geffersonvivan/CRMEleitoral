# Plano de Implementacao — CRM Eleitoral LS 2026

---

# PARTE 1 — Cruzamentos Estrategicos

Analises baseadas nos dados eleitorais 2022 do Leandro Sorgatto cruzados com dados atuais do CRM.

---

## 1. Mapa de Calor: Penetracao LS por cidade [IMPLEMENTADO]

Cruzar `votes_sorgatto_2022` / `registered_voters` = % de penetracao por cidade.

- Mostra onde LS ja e forte e onde tem potencial inexplorado
- Cidades com muitos eleitores e baixa penetracao sao oportunidades prioritarias
- Gradiente de cores: vermelho (baixa penetracao) → amarelo → verde (alta penetracao)

### Interface

Toggle no header do mapa com botoes [Regioes] e [Mapa de Calor].
Ao alternar, o mapa troca apenas as cores dos paths SVG (sem recarregar geometria).
No modo calor, a legenda de macro regioes e substituida por uma barra de gradiente com escala de valores.
O tooltip passa a exibir a % de penetracao alem dos dados atuais.
Ao clicar numa regiao e ver as cidades, o mesmo gradiente se aplica por cidade.

### Arquivos alterados

- `apps/maps/views.py` — adicionado `registered_voters` no StateMapAPI e RegionMapAPI
- `static/js/map/sc-map.js` — metodo `setHeatmap()` com D3 color scale e transicao animada
- `static/js/dashboard.js` — controle do toggle entre modos
- `templates/dashboard/index.html` — botoes toggle + legenda gradiente

---

## 2. Cidades aliadas vs adversarias (prefeito)

Cruzar `mayor_party` com desempenho LS 2022.

- Cidades com prefeito PL (ou aliado) onde LS teve poucos votos = potencial de crescimento com apoio da maquina municipal
- Cidades com prefeito de oposicao onde LS foi bem = base fiel que resiste mesmo sem apoio local
- Classificar cidades em quadrantes: aliado+forte, aliado+fraco, oposicao+forte, oposicao+fraco

---

## 3. Forca da rede PL por cidade

Cruzar `num_vereadores_pl` + prefeito PL + contatos CRM por cidade.

- Onde tem vereadores PL mas poucos contatos no CRM = rede partidaria desconectada da campanha
- Priorizar articulacao com vereadores PL em cidades com baixa presenca no CRM
- Identificar cidades com estrutura partidaria forte para alavancar

---

## 4. Ranking de zonas eleitorais

Usar dados de `ZoneResult` (votos por zona 2022) cruzados com meta 2026.

- Quais zonas deram mais votos em 2022?
- Quais zonas tem maior potencial de crescimento (gap entre votos 2022 e meta)?
- Priorizar recursos e coordenadores nas zonas com melhor custo-beneficio

---

## 5. Candidatos "vizinhos" — deputados estaduais aliados

Cruzar votos dos deputados estaduais eleitos pelo PL com votos do LS nas mesmas cidades.

- Se um dep. estadual PL teve muitos votos numa cidade onde LS teve poucos, esse deputado pode ser canal de articulacao
- Mapear quais deputados estaduais PL tem influencia em quais cidades
- Usar esses deputados como ponte para ampliar a base

---

## 6. Analise de transferencia de voto Governador → LS

Comparar votos do candidato a governador da coligacao com votos LS cidade a cidade.

- Onde o governador foi bem mas LS nao = perda de transferencia de voto
- Essas cidades precisam de trabalho de base e maior visibilidade do candidato
- Onde ambos foram bem = base consolidada, manter presenca

---

## Dados publicos do TSE para baixar e agregar

| Dado                                                         | Fonte TSE                      | Utilidade                                                                      |
| ------------------------------------------------------------ | ------------------------------ | ------------------------------------------------------------------------------ |
| Perfil do eleitorado 2022 (idade, genero, escolaridade/zona) | `perfil_eleitorado_2022.csv`   | Segmentar campanha: zonas com mais jovens, mais mulheres, maior escolaridade   |
| Votos brancos/nulos por zona 2022                            | `votacao_secao_2022_SC.csv`    | Zonas com alto voto branco/nulo = eleitores desmobilizados, potencial conquista |
| Candidatos 2022 detalhados (profissao, genero, escolaridade) | `consulta_cand_2022_SC.csv`    | Perfil dos concorrentes para posicionamento estrategico                        |

---

# PARTE 2 — Painel Kanban de Demandas por Cidade

---

## Conceito Central

Cada cidade de SC tem um pipeline de demandas que representa o trabalho necessario para conquistar aquele territorio. O kanban e um painel de guerra onde cada cartao representa uma acao concreta que aproxima o LS da meta de votos naquela cidade.

---

## Fases do Pipeline

Em vez das 3 fases atuais (A Fazer / Em Andamento / Concluida), fases que refletem o ciclo real de articulacao politica:

| Fase               | Significado                                       | Cor     |
| ------------------ | ------------------------------------------------- | ------- |
| **Planejada**      | Demanda identificada, ainda nao iniciada           | Cinza   |
| **Em Articulacao** | Contato feito, negociando apoio/agenda             | Azul    |
| **Agendada**       | Data e local definidos, aguardando execucao        | Amarelo |
| **Executada**      | Acao realizada, aguardando resultado               | Laranja |
| **Concluida**      | Resultado apurado, dados registrados               | Verde   |

---

## Estrutura da Tela

Rotas:

- `/demandas/` — visao geral (todas as cidades)
- `/demandas/?cidade=chapeco` — filtro por cidade
- `/demandas/?regiao=amosc` — filtro por regiao

### Layout

```
[Filtros: Regiao v] [Cidade v] [Responsavel v] [Prioridade v]

+-Planejada----+ +-Articulacao--+ +-Agendada-----+ +-Executada----+ +-Concluida----+
|              | |              | |               | |              | |              |
| +----------+ | | +----------+ | |               | |              | | +----------+ |
| | Chapeco  | | | | Xaxim    | | |               | |              | | | Concordia| |
| | Reuniao..| | | | Visita...| | |               | |              | | | Evento...| |
| | * 3d     | | | | 2d       | | |               | |              | | | ok 12/mai| |
| +----------+ | | +----------+ | |               | |              | | +----------+ |
|              | |              | |               | |              | |              |
+--------------+ +--------------+ +---------------+ +--------------+ +--------------+
```

Arrastar cartoes entre colunas com SortableJS (leve, sem dependencias).
Ao soltar, faz PATCH na API atualizando a fase.

---

## O Cartao (Card)

Cada cartao mostra:

- **Cidade** (destaque, com cor da macro regiao)
- **Titulo** da demanda
- **Responsavel** (avatar/nome)
- **Prazo** (dias restantes ou dias em atraso)
- **Prioridade** (borda colorida: urgente=vermelho, alta=laranja)
- **Tipo** (reuniao, evento, visita, contato, articulacao)
- **Meta vinculada** (ex: "conquistar 50 apoiadores")

---

## Tipos de Demanda

Tipos padronizados para gerar dados comparaveis:

| Tipo                       | Descricao                                        | Meta mensuravel            |
| -------------------------- | ------------------------------------------------ | -------------------------- |
| **Reuniao com lideranca**  | Encontro com prefeito, vereador, lider            | Compromisso de apoio       |
| **Evento presencial**      | Comicio, encontro, jantar                         | Numero de presentes        |
| **Visita de campo**        | Ida a cidade sem evento formal                    | Contatos adicionados       |
| **Articulacao partidaria** | Alinhamento com executiva PL local                | Vereadores engajados       |
| **Acao de comunicacao**    | Disparo WhatsApp, redes sociais local             | Alcance/respostas          |
| **Captacao de apoiador**   | Acao focada em novos apoiadores                   | Apoiadores cadastrados     |

---

## Integracao com o Mapa

Terceiro botao no toggle do mapa do Dashboard:

```
[Regioes] [Mapa de Calor] [Demandas]
```

### Modo Demandas

- Cada cidade/regiao colorida pelo status das demandas:
  - **Verde**: todas as demandas em dia
  - **Amarelo**: demandas proximas do prazo (< 3 dias)
  - **Vermelho pulsante**: demandas em atraso
  - **Cinza**: sem demandas atribuidas (ponto cego)
- Tooltip mostra: "3 demandas (1 em atraso)"
- Clicar abre o kanban filtrado naquela cidade
- Cidades cinza sao tao importantes quanto as vermelhas — significam que ninguem esta trabalhando aquele territorio

---

## Metricas do Kanban

### Painel de numeros (header do kanban)

| Metrica                      | Exemplo    |
| ---------------------------- | ---------- |
| Cidades com demandas ativas  | 87 / 295   |
| Demandas em atraso           | 12         |
| Cidades sem nenhuma acao     | 208        |
| Taxa de conclusao (mes)      | 68%        |
| Tempo medio por demanda      | 8.3 dias   |

### Por responsavel

- Quantas demandas cada coordenador tem
- Taxa de conclusao de cada um
- Cidades sob responsabilidade de cada um

### Por regiao

- Regioes com mais demandas em atraso
- Regioes sem cobertura
- Velocidade de execucao por regiao

---

## Sugestoes automaticas de demandas

Baseado nos dados que ja temos, o sistema sugere demandas:

- Cidade com penetracao < 0.5% e mais de 10.000 eleitores → sugere "Visita de campo"
- Cidade com prefeito PL mas poucos contatos CRM → sugere "Articulacao partidaria"
- Cidade com muitos vereadores PL mas sem coordenador → sugere "Reuniao com lideranca"
- Cidade sem nenhum contato no CRM → marca como ponto cego no mapa

---

## Modelo de dados (evolucao do Task atual)

O modelo `Task` atual ja tem `city`, `status`, `priority`, `due_date`, `assigned_to`. Adicionar:

- **`phase`** — substituir os 3 status por 5 fases do pipeline
- **`task_type`** — tipo padronizado (reuniao, evento, visita...)
- **`goal_description`** — meta mensuravel da demanda
- **`goal_achieved`** — resultado obtido (numerico)
- **`region`** — para filtro rapido (derivavel da cidade, mas util para queries)
- **`completed_at`** — data real de conclusao (para calcular velocidade)

---

# PARTE 3 — Roteiros de Viagem

---

## Conceito

O LS precisa visitar 295 cidades com equipe e tempo limitados. Cada viagem precisa maximizar o impacto: quantas reunioes, quantos contatos, quantas cidades cobertas por deslocamento.

Um Roteiro agrupa demandas de cidades proximas em uma unica viagem com sequencia otimizada.

---

## Exemplo de Roteiro

```
Roteiro: Oeste Catarinense — 14 a 16 de junho

Dia 1 (14/jun):
  08h  Chapeco       Reuniao com prefeito (AMOSC)
  11h  Xaxim         Visita de campo
  14h  Xanxere       Evento com liderancas
  Pernoite: Chapeco

Dia 2 (15/jun):
  08h  Concordia     Articulacao partidaria
  11h  Seara         Captacao de apoiadores
  14h  Ita           Reuniao com vereadores PL
  Pernoite: Concordia

Dia 3 (16/jun):
  08h  Joacaba       Evento presencial
  11h  Herval d'Oeste  Visita de campo
  Retorno
```

---

## Interface — `/roteiros/`

### Lista de roteiros

| Roteiro              | Periodo    | Regiao       | Cidades | Demandas | Status     |
| -------------------- | ---------- | ------------ | ------- | -------- | ---------- |
| Oeste Catarinense    | 14-16/jun  | AMOSC, AMAI  | 8       | 10       | Planejado  |
| Litoral Norte        | 20-21/jun  | AMUNESC      | 5       | 6        | Confirmado |

### Detalhe do roteiro — timeline

```
+- Dia 1: 14/jun (Sab) -------------------------------------------+
|                                                                   |
|  08:00  * Chapeco ---- Reuniao com prefeito                      |
|         |              Resp: Joao    Meta: apoio formal           |
|         |              30 min carro                               |
|  11:00  * Xaxim ----- Visita de campo                            |
|         |              Resp: Maria   Meta: 20 contatos            |
|         |              45 min carro                               |
|  14:00  * Xanxere --- Evento com liderancas                      |
|                        Resp: Carlos  Meta: 50 presentes          |
|                                                                   |
|  Pernoite: Chapeco                                                |
+-------------------------------------------------------------------+
```

---

## Vinculo com o Kanban

- Ao criar um roteiro, ele puxa demandas existentes das cidades selecionadas (fase Planejada ou Agendada)
- Ao confirmar o roteiro, as demandas mudam automaticamente para Agendada
- Ao concluir a viagem, as demandas mudam para Executada e o coordenador registra os resultados
- Demandas sem roteiro atribuido ficam no kanban esperando uma viagem

---

## Integracao com o Mapa

Quarto botao no toggle do mapa do Dashboard:

```
[Regioes] [Mapa de Calor] [Demandas] [Roteiros]
```

### Modo Roteiros

- Linhas conectando as cidades na sequencia de cada roteiro (traco sobre o mapa SVG)
- **Roteiros planejados/confirmados** — linha tracejada azul, cidades com marcador numerado
- **Roteiro em andamento** — linha solida laranja, cidade atual pulsando
- **Roteiros concluidos** — linha solida verde, mais discreta (opacidade baixa)
- Filtro acima do mapa para mostrar/ocultar concluidos
- Tooltip na linha mostra: nome do roteiro, periodo, responsavel, quantas demandas
- Tooltip na cidade mostra: hora prevista, demanda vinculada, status
- Clicar no roteiro abre o detalhe com a timeline
- Cidades que nunca apareceram em nenhum roteiro ficam sem marcador — facil ver onde o LS ainda nao passou

---

## Modelo de dados

### Roteiro

- `nome` — nome descritivo (ex: "Oeste Catarinense")
- `data_inicio` / `data_fim` — periodo da viagem
- `responsavel` — FK User (quem viaja)
- `regioes_alvo` — M2M Region
- `status` — planejado / confirmado / em_andamento / concluido
- `observacoes` — texto livre

### ParadaRoteiro (cada ponto da viagem)

- `roteiro` — FK Roteiro
- `cidade` — FK City
- `demanda` — FK Task (opcional)
- `data` — data da parada
- `hora_prevista` — horario previsto
- `ordem` — posicao na sequencia do dia
- `tempo_deslocamento` — minutos ate a proxima parada
- `pernoite` — boolean
- `observacoes` — texto livre

---

# PARTE 4 — Conteudos de Campanha

---

## Conceito

Cada visita, evento ou acao gera (ou precisa de) conteudo: posts para redes sociais, material para WhatsApp, fotos com liderancas, videos curtos, textos para disparo. O sistema organiza a producao vinculada a cada demanda do kanban.

---

## Tipos de conteudo

| Tipo                      | Quando          | Exemplo                                  |
| ------------------------- | --------------- | ---------------------------------------- |
| **Briefing**              | Antes da acao   | "Preparar arte para evento em Chapeco"   |
| **Post redes sociais**    | Antes ou depois | Texto + imagem para Instagram/Facebook   |
| **Material WhatsApp**     | Antes do disparo | Texto formatado + imagem para grupos    |
| **Registro fotografico**  | Depois da acao  | Fotos do evento/reuniao                  |
| **Video**                 | Depois da acao  | Video curto para reels/stories           |
| **Nota de imprensa**      | Depois da acao  | Release para midia local                 |

---

## Interface — aba dentro do cartao do kanban

Ao abrir uma demanda no kanban, aba Conteudos:

```
+- Reuniao com Prefeito — Chapeco --------------------------------+
|                                                                   |
|  [Detalhes]  [Conteudos (3)]  [Historico]                        |
|                                                                   |
|  +- Antes da acao ---------------------------------------------+ |
|  |  [ ] Arte para Instagram    Resp: Designer   Prazo: 12/jun  | |
|  |  [ ] Texto WhatsApp grupos  Resp: Social     Prazo: 13/jun  | |
|  +-------------------------------------------------------------+ |
|                                                                   |
|  +- Depois da acao --------------------------------------------+ |
|  |  [ ] Fotos do encontro     (pendente)                        | |
|  |  [ ] Post resultado        (pendente)                        | |
|  +-------------------------------------------------------------+ |
+-------------------------------------------------------------------+
```

---

## Painel de conteudo — `/conteudos/`

Visao independente para a equipe de comunicacao:

```
[Filtro: Pendentes v]  [Tipo v]  [Responsavel v]

Hoje (17/mai):
  [ ] Arte Instagram — Evento Chapeco (14/jun)         Designer    em producao
  [ ] Texto WhatsApp — Visita Xaxim (14/jun)           Social      pendente

Esta semana:
  [ ] Video reels — Evento Concordia (realizado 10/mai) Editor     em edicao
  [x] Post resultado — Reuniao Joacaba (08/mai)         Social     publicado
```

---

## Metricas de conteudo

| Metrica                  | O que mostra                                       |
| ------------------------ | -------------------------------------------------- |
| Conteudos pendentes      | Fila de producao da equipe de comunicacao           |
| Conteudos por demanda    | Quais acoes estao sem cobertura de comunicacao      |
| Taxa de publicacao       | % das acoes que geraram conteudo depois             |
| Cidades sem conteudo     | Territorios sem presenca digital                   |

---

## Modelo de dados

### Conteudo

- `demanda` — FK Task
- `tipo` — briefing / post_social / whatsapp / foto / video / nota_imprensa
- `fase` — antes / depois
- `titulo` — descricao curta
- `descricao` — detalhamento
- `responsavel` — FK User
- `status` — pendente / em_producao / aprovado / publicado
- `prazo` — data limite
- `arquivo` — FileField (upload da arte/foto/video, opcional)
- `url_publicacao` — link do post publicado (opcional)

---

# VISAO GERAL — Como tudo se conecta

```
MAPA (Dashboard)
  |
  |-- Modo Regioes (cores por macro regiao)           [IMPLEMENTADO]
  |-- Modo Calor (penetracao LS)                      [IMPLEMENTADO]
  |-- Modo Demandas (status do kanban)
  +-- Modo Roteiros (viagens planejadas/executadas)
        |
        | clicar na cidade
        v
KANBAN (/demandas/?cidade=chapeco)
  |
  | cada cartao
  v
DEMANDA (detalhe)
  |-- Informacoes (cidade, responsavel, prazo, meta)
  |-- Conteudos (briefing, posts, fotos)
  |-- Roteiro vinculado (viagem planejada)
  +-- Resultados (apoiadores conquistados -> atualiza CRM)
        |
        | roteiros agrupam demandas
        v
ROTEIRO (/roteiros/)
  |-- Timeline de paradas por dia
  |-- Mapa com rota entre cidades
  +-- Demandas de cada parada
```

### Ciclo completo de uma acao

1. **Mapa** mostra Chapeco cinza (sem demandas)
2. Coordenador cria demanda "Reuniao com prefeito" no **Kanban**
3. Equipe de comunicacao ve no painel de **Conteudos** que precisa preparar arte
4. Coordenador de roteiro inclui Chapeco no **Roteiro** "Oeste Catarinense"
5. Demanda muda para **Agendada**, Chapeco fica amarelo no mapa
6. Viagem acontece, demanda vai para **Executada**
7. Equipe registra fotos, publica post, registra 15 novos apoiadores
8. Demanda vai para **Concluida**, apoiadores entram no CRM
9. Chapeco fica verde no mapa, penetracao sobe no mapa de calor
