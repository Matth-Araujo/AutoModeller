# ModellerWeb & Smosh: Interface Web Automatizada para Modelagem Molecular 3D

Interface Web automatizada desenvolvida em **Django (Python 3)** para orquestrar e gerenciar experimentos de modelagem comparativa de estruturas de proteínas utilizando a biblioteca **smosh** e o **Modeller 10.7**.

---

## 🌟 Principais Funcionalidades

1. **Autenticação Flexível**:
   - **Usuário e Senha**: Cadastro e login de pesquisadores com histórico permanente de modelagens, métricas e downloads.
   - **Modo Avulso (Convidado)**: Possibilidade de executar experimentos instantaneamente sem cadastro prévio. Os experimentos avulsos ficam salvos na sessão do navegador com UUID exclusivo e podem ser vinculados à conta caso o usuário decida se cadastrar posteriormente.

2. **Linha de Montagem Automatizada (Smosh Pipeline)**:
   - **Entrada de Sequência**: Upload de arquivos (`.pir`, `.fasta`, `.txt`) ou inserção direta no formulário.
   - **Busca de Moldes (`FindTemplatesStep`)**: Varredura automática contra a base de dados de estruturas homólogas `pdb_95`.
   - **Aquisição e Preparação de Estruturas (`GetDataFromPDB` e `PDBFile`)**: Download de estruturas diretamente do Protein Data Bank (RCSB) e higienização/isolamento de cadeias e heteroátomos.
   - **Alinhamento 2D (`AlignStep`)**: Alinhamento das sequências alvo e molde gerando arquivos PIR e PAP.
   - **Modelagem Comparativa 3D (`BuildModelStep`)**: Execução do Modeller Automodel gerando 5 estruturas tridimensionais candidatas.
   - **Avaliação de Qualidade e Energia (`MakeProfile` e `EvaluateEnergy`)**: Cálculo de escores **DOPE** (Discrete Optimized Protein Energy) e **GA341**, com geração automática do gráfico comparativo de perfil energético.
   - **Refinamento de Loop Opcional (`LoopRefinementStep`)**: Refinamento fino com dinâmica molecular em regiões flexíveis ou inserções específicas.

3. **Visualizador 3D Interativo no Navegador**:
   - Integração com **3Dmol.js** (WebGL) permitindo rotação, zoom, translação e visualização em diversos estilos (*Cartoon*, *Sticks*, *Esferas*, *Superfície*) e esquemas de cores (*Espectro N&rarr;C*, *Estrutura Secundária*, *Cadeia*).
   - Alternância rápida entre qualquer um dos modelos gerados.

4. **Acompanhamento em Tempo Real**:
   - Polling assíncrono via AJAX informando a etapa atual, percentual de progresso e visualização dos logs do Modeller.
   - Captura e tratamento amigável de exceções do Modeller (`ModellerException`).

5. **Exportação e Downloads**:
   - Download individual de qualquer arquivo PDB gerado.
   - Download de pacote `.ZIP` completo contendo todos os modelos PDB, alinhamentos (`ali.ali`, `ali.pap`), gráficos DOPE e logs de execução.

---

## 📁 Estrutura do Projeto

```text
Projeto_modeller/
├── smosh/                           # Biblioteca smosh (compatibilizada com Python 3)
│   ├── ModelingStep/               # Etapas da linha de montagem
│   │   ├── FindTemplatesStep.py    # Busca de moldes no pdb_95
│   │   ├── GetSequenceFromPDBStep.py # Extração de sequências de PDBs
│   │   ├── AlignStep.py            # Alinhamento de sequências
│   │   ├── BuildModelStep.py       # Construção de modelos com automodel
│   │   ├── MakeProfile.py          # Geração de perfis DOPE
│   │   ├── EvaluateEnergy.py       # Gráficos comparativos de energia
│   │   ├── LoopRefinementStep.py   # Refinamento de loops
│   │   └── Modeller_Caller.py      # Invocador do Modeller com Python 3
│   ├── ModelingTools/              # Ferramentas auxiliares (PDBFile, AlignFile, etc.)
│   ├── Exceptions/                 # ModellerException
│   ├── pdb/                        # Base pdb_95 (.pir e .bin)
│   ├── files/                      # Arquivos de dados de teste (ex: TvLDH)
│   └── *_test.py                   # Testes automatizados do smosh (should_dsl)
├── modeller_web/                    # Projeto Django
│   ├── manage.py
│   ├── modeller_web/               # Configurações do Django (settings, urls, wsgi)
│   ├── experiments/                # Aplicação de experimentos
│   │   ├── models.py               # Modelos: Experiment, ExperimentResultModel, TemplateCandidate
│   │   ├── views.py                # Views: Home, Criação, Detalhes, Polling, Download ZIP, Auth
│   │   ├── services.py             # Orquestrador da esteira smosh / Modeller
│   │   ├── forms.py                # Formulários de experimentos e cadastro
│   │   ├── urls.py                 # Rotas da aplicação
│   │   ├── admin.py                # Painel administrativo
│   │   └── tests_should_dsl.py     # Testes automatizados da interface com should_dsl
│   └── templates/                  # Templates HTML modernos (Bootstrap 5 + 3Dmol.js)
│       ├── base.html
│       ├── experiments/
│       │   ├── home.html
│       │   ├── experiment_form.html
│       │   ├── experiment_detail.html
│       │   └── experiment_list.html
│       └── registration/
│           ├── login.html
│           └── register.html
└── README.md
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
- **Python 3.10+** (testado e homologado no Python 3.13)
- **Modeller 10.7** instalado no sistema operacional (com licença acadêmica configurada)
- Pacotes Python:
  ```bash
  pip install django should_dsl matplotlib numpy
  ```

### 2. Inicializar o Banco de Dados
No diretório `modeller_web`:
```bash
cd /home/matheus/IC/Projeto_modeller/modeller_web
python3 manage.py migrate
```

### 3. Iniciar o Servidor Web
```bash
python3 manage.py runserver 0.0.0.0:8000
```
Acesse no seu navegador: **`http://localhost:8000`**

### 4. Acesso Administrativo (Opcional)
Um usuário administrador já foi pré-configurado para inspeção pelo painel Django Admin:
- **URL**: `http://localhost:8000/admin/`
- **Usuário**: `admin`
- **Senha**: `admin123`

---

## 🧪 Executando os Testes Automatizados

O projeto utiliza **`should_dsl`** e **`unittest`** para validação automatizada de todas as camadas.

### 1. Testes da Interface Django (`should_dsl`)
Para validar os modelos, propriedades de convidados (modo avulso), endpoints de API e views:
```bash
cd /home/matheus/IC/Projeto_modeller/modeller_web
python3 manage.py test experiments.tests_should_dsl
```

### 2. Testes da Biblioteca Smosh (`should_dsl`)
Para rodar os testes unitários do smosh:
```bash
cd /home/matheus/IC/Projeto_modeller
python3 -m unittest smosh/ModelingStep_test.py
python3 -m unittest smosh/ProteinStructureFile_test.py
python3 -m unittest smosh/GetSequenceFromPDBStep_test.py
python3 -m unittest smosh/MakeProfile_test.py
python3 -m unittest smosh/EvaluateEnergy_test.py
python3 -m unittest smosh/EvaluateEnergyofLoopRefinementStep_test.py
python3 -m unittest smosh/ModellerException_test.py
```

---

## 🔬 Como Usar a Interface Web

1. **Experimento Rápido com Exemplo (TvLDH)**:
   - Na página inicial, clique em **"Carregar Exemplo (TvLDH)"**.
   - O formulário será preenchido automaticamente com os parâmetros e sequência da Lactato Desidrogenase.
   - Clique em **"Iniciar Modelagem Automatizada"**.
   - Acompanhe a esteira em tempo real: busca de molde no `pdb_95` (1bdm), extração da sequência, alinhamento, modelagem 3D dos 5 modelos e cálculo do perfil DOPE.
   - Ao término, inspecione a estrutura 3D interativa diretamente na tela, alterne estilos (*Cartoon*, *Superfície*), verifique a tabela de escores e baixe o PDB do melhor modelo ou o arquivo ZIP com tudo.

2. **Experimento com Nova Sequência**:
   - Clique em **"Novo Experimento"** ou **"Iniciar Experimento Avulso"**.
   - Preencha o identificador e cole sua sequência em formato **PIR** ou **FASTA** (ou faça upload do arquivo).
   - Opcionalmente, ative o **Refinamento de Loop** informando os resíduos inicial e final.
   - Inicie a modelagem.

3. **Gerenciamento de Conta**:
   - Crie uma conta ou faça login para manter salvo o histórico de todas as modelagens.
   - Caso realize experimentos em modo avulso antes de entrar, o sistema detectará automaticamente e oferecerá o botão **"Vincular à minha conta"**.
