# AutoModeller WEB: Plataforma Automatizada para Modelagem Molecular 3D

Plataforma Web automatizada de alto desempenho desenvolvida em **Django (Python 3)** para orquestrar e gerenciar experimentos de modelagem comparativa de estruturas tridimensionais de proteínas utilizando o **Modeller 10.7**.

---

## 🌟 Principais Funcionalidades

1. **Autenticação Direta por E-mail**:
   - **Login com E-mail**: Cadastro simplificado solicitando apenas nome e e-mail (dispensando nome de usuário separado).
   - **Modo Avulso (Convidado)**: Possibilidade de executar experimentos instantaneamente sem cadastro prévio. Os experimentos avulsos ficam salvos na sessão do navegador com UUID exclusivo e podem ser vinculados à conta com 1 clique caso o usuário decida se cadastrar posteriormente.

2. **Fluxo 100% Automatizado**:
   - **Entrada Descomplicada**: Basta colar a sequência (PIR ou FASTA) ou enviar um arquivo. O título, formato e o identificador da proteína são reconhecidos e higienizados automaticamente sem exigir preenchimento manual de código ou seleção de refinamento.
   - **Busca de Moldes**: Varredura automática contra a base de dados de estruturas homólogas `pdb_95`.
   - **Aquisição e Preparação de Estruturas**: Download de estruturas diretamente do Protein Data Bank (RCSB) e higienização/isolamento de cadeias e heteroátomos.
   - **Alinhamento 2D**: Alinhamento das sequências alvo e molde gerando arquivos PIR e PAP.
   - **Modelagem Comparativa 3D**: Execução do Modeller Automodel gerando estruturas tridimensionais candidatas com a licença acadêmica oficial (`MODELIRANJE`).
   - **Avaliação de Qualidade e Energia**: Cálculo de escores **DOPE** (Discrete Optimized Protein Energy) e **GA341**, com geração automática do gráfico comparativo de perfil energético.

3. **Visualizador Molecular 3D Integrado (3Dmol.js HTML5 / WebGL)**:
   - Visualizador molecular interativo WebGL puro no navegador via **3Dmol.js**, sem necessidade de instalação local de PyMOL ou VMD.
   - Controles de rotação automática (*spin*), zoom, translação e visualização em diversos estilos (*Cartoon*, *Sticks*, *Esferas*, *Superfície*) e esquemas de cores (*Espectro N&rarr;C*, *Estrutura Secundária*, *Cadeia*).
   - **Vitrine de Estruturas 3D em Destaque na Página Inicial**: Carrossel com transição automática ("estruturas passando") exibindo modelos tridimensionais com rotação contínua e informações estruturais.

4. **Comparação Alvo vs Template e Inspeção 3D em "Meus Experimentos"**:
   - Tabela com botão **`+` expansível** em cada experimento.
   - Ao expandir, exibe lado a lado:
     - **Comparação de Sequências**: Exibição do alinhamento oficial Modeller PAP pareando resíduo a resíduo a sequência inserida contra o molde cristalográfico template.
     - **Visualizador 3Dmol**: Renderização interativa imediata do melhor modelo 3D com rotação ativada.

5. **Acompanhamento em Tempo Real**:
   - Polling assíncrono via AJAX informando a etapa atual, percentual de progresso e visualização dos logs do Modeller.
   - Captura e tratamento amigável de exceções do Modeller (`ModellerException`).

6. **Exportação e Downloads**:
   - Download individual de qualquer arquivo PDB gerado.
   - Download de pacote `.ZIP` completo contendo todos os modelos PDB, alinhamentos (`ali.ali`, `ali.pap`), gráficos DOPE e logs de execução.

---

## 📁 Estrutura do Projeto

```text
Projeto_modeller/
├── smosh/                           # Módulos científicos do pipeline Modeller
│   ├── ModelingStep/               # Etapas automatizadas (busca, alinhamento, automodel, perfis)
│   ├── ModelingTools/              # Ferramentas de manipulação de PDB e alinhamentos
│   ├── Exceptions/                 # ModellerException
│   ├── pdb/                        # Base pdb_95 (.pir e .bin)
│   └── files/                      # Arquivos de dados de teste (ex: TvLDH)
├── modeller_web/                    # Aplicação Web Django
│   ├── manage.py
│   ├── static/pdb/                 # Estruturas PDB estáticas para vitrine 3Dmol
│   ├── templates/                  # Templates HTML5 (Bootstrap 5 + 3Dmol.js)
│   │   ├── base.html               # Layout principal e navbar AutoModeller WEB
│   │   ├── experiments/
│   │   │   ├── home.html           # Vitrine 3D "estruturas passando" e início
│   │   │   ├── experiment_form.html# Formulário automático simplificado
│   │   │   ├── experiment_list.html# Lista com botão (+) de comparação e 3D
│   │   │   └── experiment_detail.html # Detalhes, progresso e visualizador
│   │   └── registration/           # Login e cadastro com e-mail
│   ├── experiments/
│   │   ├── backends.py             # Autenticação via EmailBackend
│   │   ├── forms.py                # Auto-detecção de sequência e cadastro sem username
│   │   ├── models.py               # Modelos e propriedades de alinhamento
│   │   ├── services.py             # Pipeline assíncrona com chave MODELIRANJE
│   │   └── views.py                # Controladores web
│   └── modeller_web/settings.py    # Configurações do Django e Modeller
├── Dockerfile                       # Imagem Docker com Modeller 10.7 e Python 3
├── docker-compose.yml               # Orquestração do contêiner com portas e volumes
└── requirements.txt                 # Dependências Python
```

---

## 🚀 Como Executar

### 1. Via Docker Compose (Recomendado)

```bash
cd /home/matheus/IC/Projeto_modeller
docker-compose up --build
```
Acesse a aplicação no navegador em: `http://localhost:8080` (ou na porta configurada em `$PORT`).

### 2. Execução Local

```bash
cd /home/matheus/IC/Projeto_modeller/modeller_web
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
Acesse em: `http://localhost:8000`

---

## 🧪 Testes Automatizados

A suíte de testes cobre a validação dos modelos, extração de dados, views e formulários automáticos:

```bash
python modeller_web/manage.py test experiments
```
