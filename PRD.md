# PRD - Escala Louvor

## 1) Visao geral

O Escala Louvor e uma aplicacao para organizar grupos de louvor, membros, repertorio e eventos, com backend Django REST e frontend Flet.

O produto resolve o problema de organizacao descentralizada (planilhas, mensagens e memoria informal), centralizando:
- cadastro e administracao de grupos;
- gerenciamento de membros por funcao;
- biblioteca de musicas por grupo;
- eventos com participantes e setlist;
- controle de acesso por papel dentro de cada grupo.

## 2) Objetivo do produto

Entregar um sistema simples, seguro e multi-grupo para planejamento de escalas de louvor, reduzindo retrabalho operacional e falhas de comunicacao entre lideres e musicos.

## 3) Objetivos de negocio

- Reduzir tempo medio de montagem de escala semanal.
- Aumentar previsibilidade de participacao dos membros.
- Manter historico estruturado de repertorio por grupo.
- Garantir isolamento de dados entre grupos.

## 4) Publico-alvo

### 4.1 Persona: Administrador do grupo
- Perfil: lider/coordenador de ministerio.
- Necessidades:
  - criar e configurar grupos;
  - adicionar/remover membros;
  - manter repertorio;
  - criar eventos e definir participantes/musicas.

### 4.2 Persona: Membro do grupo
- Perfil: vocalista/instrumentista.
- Necessidades:
  - visualizar informacoes do grupo;
  - visualizar eventos e repertorio;
  - atualizar participacao em eventos (confirmado/recusado/pendente).

## 5) Escopo

### 5.1 Escopo MVP (incluido)
- Autenticacao JWT (login, refresh, me, alteracao de senha).
- Listagem e criacao de grupos.
- Edicao de configuracoes do grupo (nome, descricao, slug).
- Gerenciamento de membros por grupo.
- Gerenciamento de musicas por grupo.
- Visualizacao de grupo com:
  - abas de membros e musicas;
  - carrossel de eventos no detalhamento.
- Endpoints de eventos, membros de evento e setlist.

### 5.2 Fora de escopo (agora)
- Notificacoes push/email/whatsapp.
- Integracao com calendario externo.
- Modo offline.
- Permissoes ultra-granulares por recurso.
- Dashboard analitico avancado.

## 6) Requisitos funcionais

### RF-01 Autenticacao
- O usuario deve realizar login com usuario/senha.
- O sistema deve renovar token automaticamente via refresh.
- O sistema deve invalidar sessao no frontend quando refresh falhar.

### RF-02 Grupos
- Usuario autenticado deve listar apenas grupos dos quais e membro.
- Usuario autenticado deve poder criar grupo.
- Criador do grupo deve entrar automaticamente como admin.
- Membro do grupo deve visualizar dados do grupo.
- Apenas admin do grupo pode editar dados do grupo.

### RF-03 Membros do grupo
- Membro do grupo pode listar membros.
- Apenas admin pode adicionar/remover membros.
- Cada membro deve possuir papel (admin/member) e instrumento.

### RF-04 Musicas do grupo
- Membro do grupo pode listar musicas.
- Apenas admin pode criar/editar/remover musicas.
- Musica deve conter no minimo titulo; artista/chave/notas/link sao opcionais.

### RF-05 Eventos
- Membro do grupo pode listar eventos do grupo.
- Apenas admin pode criar/editar/remover evento.
- Evento deve suportar titulo, data e descricao.

### RF-06 Participacao em evento
- Admin pode alocar/remover membros no evento.
- Membro alocado deve poder atualizar propria participacao:
  - pending
  - confirmed
  - declined

### RF-07 Setlist de evento
- Membro do grupo pode visualizar musicas do evento.
- Apenas admin pode adicionar/remover/reordenar musicas do evento.

### RF-08 Navegacao frontend
- Sistema deve iniciar em login quando nao autenticado.
- Sistema deve redirecionar para dashboard apos autenticacao.
- Dashboard deve permitir:
  - abrir grupos;
  - criar grupo;
  - abrir tela de configuracao de grupo.

### RF-09 Carrossel de eventos no grupo
- Ao entrar no detalhamento do grupo, o usuario deve visualizar carrossel horizontal de eventos.
- Cada card de evento deve exibir titulo, data, descricao resumida e contadores de membros/musicas.
- Em ausencia de eventos, exibir estado vazio explicito.

## 7) Requisitos nao funcionais

### RNF-01 Seguranca
- Controle de acesso obrigatorio por endpoint.
- Nao confiar em filtros vindos do cliente para escopo de grupo.
- Tokens com expiracao curta e refresh rotativo.
- Segredos fora do codigo-fonte (env vars).

### RNF-02 Arquitetura e qualidade
- Seguir SOLID e Clean Architecture.
- Separacao clara entre Models, Views, Serializers e Permissions.
- Frontend com componentes reutilizaveis.

### RNF-03 Performance
- Tempo de resposta alvo para listagens comuns: ate 500 ms em ambiente local padrao.
- Consultas com filtro por grupo e uso de select_related/prefetch quando aplicavel.

### RNF-04 Confiabilidade
- Tratamento padrao de erros de API no frontend.
- Mensagens de erro amigaveis para casos esperados.

## 8) Regras de negocio e permissao

- Regra RB-01: recursos sao sempre isolados por grupo.
- Regra RB-02: admin do grupo pode alterar estrutura (membros, musicas, eventos).
- Regra RB-03: membro comum pode consumir dados e interagir apenas no que for permitido.
- Regra RB-04: usuario fora do grupo nao deve acessar recursos do grupo.

## 9) Fluxos principais

### F-01 Login e acesso inicial
1. Usuario informa credenciais.
2. Frontend recebe tokens e consulta perfil.
3. Usuario e redirecionado ao dashboard.

### F-02 Criacao e configuracao de grupo
1. Admin cria grupo.
2. Grupo aparece no dashboard.
3. Admin abre configuracao e atualiza nome/descricao/slug.

### F-03 Operacao de grupo
1. Usuario entra no detalhamento do grupo.
2. Visualiza carrossel de eventos.
3. Navega para abas de membros e musicas para gestao/listagem.

## 10) Metricas de sucesso

- MS-01: tempo medio para criar grupo e adicionar 1 membro <= 2 minutos.
- MS-02: taxa de erro 4xx inesperado no frontend < 2% das requisicoes.
- MS-03: 90% dos grupos ativos com ao menos 1 evento cadastrado em 30 dias.
- MS-04: 95% das operacoes de leitura com resposta < 500 ms (ambiente homologacao).

## 11) Criterios de aceite (release atual)

- CA-01: usuario autenticado acessa dashboard sem erro de compatibilidade Flet.
- CA-02: menu do dashboard abre tela de configuracao de grupo.
- CA-03: tela de configuracao atualiza grupo com feedback de sucesso/erro.
- CA-04: ao abrir um grupo, carrossel de eventos e exibido.
- CA-05: sistema mostra estado vazio quando nao houver eventos.
- CA-06: endpoints respeitam permissao de membro/admin.

## 12) Riscos e mitigacoes

- R-01 Incompatibilidade de versao Flet.
  - Mitigacao: padronizar API usada (`ft.icons`, drawer por estado `open`).
- R-02 Crescimento de regras de permissao sem cobertura de testes.
  - Mitigacao: ampliar suite de testes de autorizacao por endpoint.
- R-03 Divergencia entre UX desktop/web no Flet.
  - Mitigacao: validar fluxos criticos em ambos os modos de execucao.

## 13) Roadmap sugerido

### Fase 1 (curto prazo)
- CRUD completo de eventos no frontend.
- Associacao de membros e musicas por evento com UI dedicada.
- Melhorias de UX no carrossel (filtros e navegacao guiada).

### Fase 2 (medio prazo)
- Notificacoes de participacao.
- Confirmacao de presenca com lembretes.
- Indicadores basicos de frequencia por membro.

### Fase 3 (longo prazo)
- Integracoes externas (calendario e mensageria).
- Multi-tenant mais robusto para operacao em escala.

## 14) Dependencias tecnicas

- Python 3.10+
- Django + DRF + SimpleJWT
- Flet
- Poetry

## 15) Premissas

- Uso inicial em contexto de grupos locais com volume moderado.
- Conectividade com backend disponivel para operacao normal.
- Estrategia de autenticacao baseada exclusivamente em JWT.
