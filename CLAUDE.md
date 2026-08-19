# CLAUDE.md — Regras de Projeto

Repositório: https://github.com/Controladoria-MG/Analise-de-Balanco (público, criado em 2026-08-18).

## Estrutura de Diretórios

```
Raiz/
├── index.html
├── .gitignore
├── .env / .env.example
├── CLAUDE.md
├── documentacao.txt
├── requirements.txt
├── static/
│   ├── script.js
│   └── style.css
├── data/
│   └── analise_balanco/
└── backend/
    ├── radar_fechamento.py      (robô 1 — MGApps, pywinauto)
    ├── retorno_checklist.py     (robô 2 — Intranet, selenium)
    ├── resumo.py                (junta as duas exportações)
    └── orquestrador.py          (roda os 2 robôs + resumo.py + gera os JSONs do portal)
```

---

## Regras — OBRIGATÓRIO SEGUIR

### HTML
- O único arquivo `.html` do projeto é `index.html`, localizado **sempre na raiz**.
- **NUNCA** crie outros arquivos `.html` em subpastas.
- **NUNCA** escreva CSS ou JS inline dentro do HTML. Use os arquivos em `static/`.

### CSS e JS
- Todo `.css` e `.js` fica **exclusivamente** em `static/`.
- **NUNCA** crie subpastas dentro de `static/`.
- **NUNCA** misture lógica de backend com arquivos de `static/`.

### Dados (`data/`)
- **NUNCA** salve arquivos diretamente na raiz de `data/`.
- Todo arquivo de dados fica dentro de `data/analise_balanco/`.
- Arquivos gerados:
    - `radar_fechamento.xlsx` — exportação bruta do MGApps "Analise Balanço" (aba única "Radar", 17 colunas: `IdCliente, Cliente, Grupo, Gerente, Tributacao, DataImportacao, DataSimulacao, Data, DataFechamento, ResponsavelManipulacao, EquipeAtendimento, Status, Unidade, Segmento, Mes, Ano, FechamentoBranco`).
    - `retorno_checklist.xlsx` — exportação bruta da Intranet, **2 abas**: `Totalizador` (resumo agregado, não usado) e `Pendencias` (a real — colunas incluem `CodCliente, RazaoSocial, Status, DataBaixa, ...`; ler sempre `sheet_name="Pendencias"`).
    - `resumo.xlsx` — as duas juntas por `IdCliente`=`CodCliente` (não por nome — nomes têm duplicidade), regra de "Documentação" em `backend/resumo.py` (chave já atualizada em 2026-08-18).
    - `analise_balanco_dados.json` — subconjunto de colunas do resumo para o portal ler via `fetch`.
    - `status.json` — `{ultima_execucao, registros}`.

### Backend (`backend/`)
Dois robôs, tecnologias diferentes (igual ao raciocínio do [[project_radar_fiscal]] — Selenium não serve para o app desktop MGApps, mas serve para a Intranet que é uma página web comum):

- `radar_fechamento.py`: automatiza o app desktop **"Analise Balanço.exe"** (separado do "Sistema de Analise" do Radar Fiscal, aberto pelo tile "Analise Balanço" do MGApps), via **pywinauto**. Não pede login próprio (usa sessão já autenticada) — `MGAPPS_USUARIO`/`MGAPPS_SENHA` no `.env` não são usados por este robô hoje. Fluxo calibrado ao vivo: clicar no ícone de pessoa da barra lateral (`ListItem` índice 1) abre o painel `auto_id="Radar"`; filtros de Mês/Ano são os `children()` de índice 0/1/2 do `Group` interno (sem nomes úteis — usar posição, não título); botão "Exportar" (dentro do dropdown do `MenuItem` "Arquivo") não tem nome acessível via UIA — clicado por coordenada relativa à janela `(128, 172)`, confirmado pelo diálogo "Selecionar pasta" aparecendo de fato; esse diálogo aceita Ctrl+L + caminho digitado. **Sempre fecha a janela "Análise de Balanço" sozinho** — no início de `executar()` (se já estava aberta de uma execução anterior/crash/uso manual, fecha antes de começar do zero) e no fim, dentro de um `finally` (fecha mesmo se a extração falhar no meio). Detalhes completos e problemas conhecidos em `documentacao.txt`.
- `retorno_checklist.py`: automatiza a **Intranet** (`https://aplicativo.mgcontecnica.com.br/#/home`, via **selenium**) — login > MG Controle > Relatórios > Personalizados > item de texto exato `"(Meu)Retorno do Checklist"` (sem espaço; existe uma variante "(EF)" no mesmo menu) > competência do mês anterior calculada automaticamente > exporta. Baseado no script de referência `Utilitarios/Utilitarios/3 - Relatório_Personalizado.py` (fora deste projeto).
- `resumo.py`: junta os dois exports por `IdCliente`/`CodCliente` (não por nome de empresa). Ver regra de status em `documentacao.txt`.
- `orquestrador.py`: chama `radar_fechamento.executar()` + `retorno_checklist.executar()` + `resumo.gerar_resumo()`, depois gera `analise_balanco_dados.json` (subconjunto de colunas em `COLUNAS_PORTAL` — hoje só `Cliente`/`Documentação`, o que o portal usa) e `status.json`. É o ponto de entrada pra rodar o pipeline inteiro: `python backend/orquestrador.py`.
- **Não existe backend web** — o portal é 100% estático (lê os JSONs via `fetch`), seguindo o padrão dos outros portais MG feitos só com robô local + página estática.
- **NUNCA** importe ou referencie arquivos de `static/` a partir do backend.

### `.gitignore`
- Inclui obrigatoriamente `.env`, `__pycache__/`, `*.log`, `.venv/` e os arquivos gerados em `data/analise_balanco/`.
- **NUNCA** versione credenciais.

### Como rodar (previsto)
```
cd Analise-de-Balanco
python -m http.server 8792
```
Acessar `http://localhost:8792` (fetch de arquivo local via `file://` é bloqueado por CORS).

### Dashboard (cards + evolução diária + ranking) — 2026-08-19
`index.html` + `static/script.js` foram reconstruídos **espelhando o Radar Fiscal** (mesmo `static/style.css`, copiado de lá): filtro de Unidade em chips no topo, filtros gerais (busca/Segmento/Tributação/Status/Documentação/Gerente), duas abas de cards ("Por Tributação" e "Por Segmento" — `Segmento` faz o papel que `DeptoFiscal` fazia no Radar Fiscal, já que este projeto não tem coluna de departamento; o card de Segmento é aninhado por Tributação, igual Depto era aninhado por Regime), ranking "Pendências por Gerente" (top 10, clicável) e a seção "Evolução Diária" (barra por dia, SVG desenhado à mão).
- **Única diferença pedida explicitamente pelo usuário**: a "Evolução Diária" usa `DataImportacao` (primeira importação da empresa no Analise Balanço.exe) em vez de `DataConfirmacao` (que não existe neste projeto).
- `STATUS_ORDEM` em `static/script.js` usa os 5 valores reais de `Status` (`Fechado, Importado Contábil, Simulando, OK - Com GC, Não Importado`) — contagem sempre pela chave real. **`STATUS_ROTULOS` (2026-08-19)** ajusta só a grafia exibida nos cards pra bater com o Radar Fiscal onde o significado é o mesmo: `"OK - Com GC"→"Com o GC"`, `"Não Importado"→"Não importado"`; `"Fechado"`/`"Simulando"` já batiam; `"Importado Contábil"` fica como está (sem correspondência no Radar Fiscal, não inventei uma). Decisão do usuário: "só ajustar texto/grafia", não forçar os 5 rótulos do Radar Fiscal por posição.
- **Seção "Evolução Diária" (2026-08-19)**: descrições trocadas de "importadas" para "fechadas" pra bater com o Radar Fiscal — subtítulo "Empresas fechadas por dia", tooltip da barra "... fechado(s)", `aria-label="Fechamentos por dia"`. A mensagem de vazio (menos de 2 dias) continua citando "Primeira Importação" (referência técnica ao campo `DataImportacao`, não uma descrição genérica — fora do escopo do pedido).
- **`Tributacao` e `Status` agora recebem a mesma limpeza do Radar Fiscal (2026-08-19, a pedido do usuário: "preciso tratar os dados da mesma forma que é tratado no radar fiscal")** — implementada em `backend/resumo.py` (`MAPA_TRIBUTACAO`, dentro de `processar_resumo`), não no frontend: `Tributacao` perde o prefixo "Federal -" e colapsa as 3 variantes de Lucro Real (`L Real -Trimestral`/`L.Real - Mensal`/`Lucro Real - Anual`) num único grupo "Lucro Real", igual ao `MAPA_REGIME` do Radar Fiscal; `Status` vazio/nulo vira "Não Importado" (defensivo — na prática a exportação já vem sem nulos). `regimeCurto()` no `script.js` continua existindo só como defesa (a coluna já chega sem o prefixo do backend).
- **Sem exclusão de Unidade**: o Radar Fiscal remove "MG EXPRESS" de `dados` (`UNIDADES_EXCLUIDAS`) por uma regra de negócio própria dele; aqui todas as unidades aparecem (incluindo MG EXPRESS) — decisão consciente, não copiada sem necessidade. Avisar se o usuário quiser a mesma exclusão.
- `backend/orquestrador.py`: `COLUNAS_PORTAL` ampliado de `["Cliente", "Documentação"]` para `["IdCliente", "Cliente", "Grupo", "Unidade", "Segmento", "Gerente", "Tributacao", "Status", "Documentação", "DataImportacao"]`, e `_gerar_json_portal` passou a tratar `pd.Timestamp`/`NaT` (serializa `DataImportacao` como ISO 8601), igual ao Radar Fiscal — antes só tratava `NaN` float.
- `static/logo.png` copiado do Radar Fiscal (mesma marca MG Contabilidade) para o header usar o mesmo layout com logo.

### Cores — regra fixa
**Nunca verde/âmbar para status.** Só rampa de vermelho MG, igual a todos os outros dashboards MG — ver [[feedback_mg_dashboards_red_only_palette]].

---

## Status atual (2026-08-19)

- `backend/retorno_checklist.py`: **pronto e testado** contra o site real.
- `backend/radar_fechamento.py`: **pronto e testado** — pipeline completo validado ao vivo do zero até a exportação real. Nessa validação apareceram (e foram corrigidos) mais dois bugs além dos "problemas conhecidos" antigos: `_selecionar_combo` dava falso negativo lendo o `Edit` interno do ComboBox (sempre vazio — corrigido pra usar `combo.selected_text()`), e `_dropdown_arquivo_aberto` dava falso positivo com a grade de resultados populada (removido — `_exportar` agora confirma pelo efeito real: o diálogo "Selecionar pasta" aparecendo). Também endurecido contra retry de foco de janela e estação bloqueada (Win+L). Ver `documentacao.txt` para detalhes de cada bug.
- `backend/resumo.py`: **pronto e testado** — chave de junção `IdCliente`/`CodCliente` validada ponta a ponta com os dois arquivos reais: 2114 linhas, 1422 "Documentação Recebida" / 692 "Documentação Pendente" (`data/analise_balanco/resumo.xlsx`).
- `index.html` + `static/`: dashboard completo (não mais o portal básico de KPIs/tabela) — reconstruído em 2026-08-19 espelhando o Radar Fiscal, ver seção "Dashboard" acima. Lê `data/analise_balanco/analise_balanco_dados.json` + `status.json`.
- `backend/orquestrador.py`: **pronto** — gera os dois JSONs a partir do `resumo.xlsx`. Testada a etapa de junção+geração de JSON com os dados reais já baixados (2114 registros). Não há mais passo maior bloqueado no projeto.

Ver `documentacao.txt` para o fluxo completo calibrado, colunas reais confirmadas e o que falta ("Dúvidas em aberto" / "Problemas conhecidos").
