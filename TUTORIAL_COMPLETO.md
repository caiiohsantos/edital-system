# EDITAL SYSTEM — Guia Completo para Leigos
## Do zero ao cliente recebendo o app

---

# PARTE 1 — O QUE FICA DENTRO DO EXECUTAVEL

Quando voce roda o `build.bat`, ele cria uma pasta `dist\EditalSystem\`
com TUDO que o cliente precisa para rodar. Estrutura:

```
dist\EditalSystem\
  EditalSystem.exe        <- o programa em si (cliente clica aqui)
  core\                   <- logica interna (nao mexe)
  client\                 <- logica do app (nao mexe)
  tutoriais\              <- pasta VAZIA (videos ficam no GitHub)
  tutorials.json          <- lista de tutoriais (atualizada pelo admin)
  version.json            <- versao atual do app
  blocked_serials.json    <- lista de licencas bloqueadas
  Qt6*.dll, etc           <- arquivos do sistema (necessarios)
```

O cliente recebe a pasta `EditalSystem\` inteira compactada.
Ele descompacta e clica em `EditalSystem.exe`. So isso.

---

# PARTE 2 — GERAR O EXECUTAVEL (BUILD)

## Prerequisitos (so na primeira vez)

1. Tenha rodado o `setup_dev.bat` antes
2. O `venv\` precisa existir na pasta do projeto

## Como buildar

1. Abra a pasta do projeto `edital_system`
2. Clique duas vezes em **`build.bat`**
3. Aguarde (pode demorar 3-5 minutos)
4. Ao terminar aparece:
   ```
   BUILD FINALIZADO COM SUCESSO!
   CLIENTE: dist\EditalSystem\EditalSystem.exe
   ADMIN:   dist\EditalAdmin\EditalAdmin.exe
   ```

## O que fazer apos o build

- A pasta `dist\EditalSystem\` e o que voce distribui para clientes
- A pasta `dist\EditalAdmin\` e so sua, nunca entregue para cliente
- Compacte `EditalSystem\` em .zip e envie para o cliente

---

# PARTE 3 — CONFIGURAR O GITHUB (UMA VEZ SO)

O GitHub serve para 3 coisas:
- Guardar o codigo-fonte
- Hospedar os videos dos tutoriais (aba Releases)
- Sincronizar a lista de tutoriais e versoes com os clientes

## Passo 1 — Criar conta e repositorio

1. Acesse **github.com** e crie uma conta gratuita
2. Clique no botao verde **"New"** no canto superior esquerdo
3. Nome do repositorio: `edital-system`
4. Marque **"Private"** (so voce ve o codigo)
5. Clique **"Create repository"**
6. Copie o link que aparece: `https://github.com/SEU_USUARIO/edital-system.git`

## Passo 2 — Instalar o Git

1. Acesse **git-scm.com/download/win**
2. Baixe e instale (pode clicar "Next" em tudo)
3. Ao terminar, clique com botao direito dentro da pasta
   `edital_system` no Windows Explorer
4. Clique em **"Open Git Bash here"**

## Passo 3 — Subir o projeto pela primeira vez

No Git Bash que abriu, cole esses comandos UM POR UM:

```bash
git init
git add .
git commit -m "versao inicial"
git remote add origin https://github.com/SEU_USUARIO/edital-system.git
git push -u origin master
```

Quando pedir usuario e senha:
- Usuario: seu usuario do GitHub
- Senha: um TOKEN (nao a senha normal)

## Como gerar o Token (senha do Git)

1. GitHub -> clique na sua foto (canto superior direito)
2. **Settings** -> **Developer settings** (menu lateral esquerdo, la no fundo)
3. **Personal access tokens** -> **Tokens (classic)**
4. **Generate new token (classic)**
5. Em "Note" escreva: `edital-system`
6. Marque a caixa **`repo`**
7. Clique **Generate token**
8. COPIE O TOKEN AGORA (ele so aparece uma vez)
9. Use esse token como senha quando o Git pedir

## Passo 4 — Configurar as URLs no codigo

Abra o arquivo `core\tutorials_sync.py` no Bloco de Notas e edite:

```python
GITHUB_TUTORIALS_URL = "https://raw.githubusercontent.com/SEU_USUARIO/edital-system/master/tutorials.json"
GITHUB_VERSION_URL   = "https://raw.githubusercontent.com/SEU_USUARIO/edital-system/master/version.json"
```

Substitua `SEU_USUARIO` pelo seu usuario real do GitHub.

Salve o arquivo e faca o push:
```bash
git add .
git commit -m "configura URLs do GitHub"
git push
```

---

# PARTE 4 — SUBIR VIDEOS DOS TUTORIAIS

Os videos ficam na aba **Releases** do GitHub — gratuito, sem limite.

## Como subir um video

1. Acesse seu repositorio no GitHub
2. No menu lateral direito clique em **"Releases"**
3. Clique em **"Create a release"**
4. Em "Tag version" escreva: `tutoriais-v1`
5. Em "Release title" escreva: `Videos dos Tutoriais`
6. Arraste seus arquivos `.mp4` para a area de upload
7. Aguarde o upload terminar
8. Clique **"Publish release"**

## Como pegar o link do video

1. Clique no nome do video na release
2. O link sera algo assim:
```
https://github.com/SEU_USUARIO/edital-system/releases/download/tutoriais-v1/detran_mg.mp4
```
3. Copie esse link

## Como configurar o tutorial no admin

1. Abra o `run_admin.bat`
2. Va em **"Editais / Tutoriais"**
3. Clique em **"Editar"** no edital desejado
4. Cole o link do GitHub Releases
5. Salve

## Como os clientes recebem os videos

Apos salvar no admin, o `tutorials.json` e atualizado automaticamente.
Voce precisa subir esse arquivo para o GitHub:

```bash
git add tutorials.json
git commit -m "atualiza tutoriais"
git push
```

Da proxima vez que o cliente abrir o app, ele busca o `tutorials.json`
do GitHub e os videos aparecem automaticamente.
O cliente clica em "Tutorial" -> o video toca diretamente via streaming.
NAO precisa baixar nada.

---

# PARTE 5 — GERENCIAR LICENCAS

## Criar licenca para um cliente

1. Abra `run_admin.bat`
2. Va em **"Usuarios"**
3. Clique **"+ Novo Usuario"**
4. Preencha nome e email do cliente
5. Define quantos dias de validade (padrao: 30)
6. Clique **"Gerar"** para criar o serial key
7. Clique **"Salvar"**
8. Clique no icone **📄** para exportar o arquivo `.lic`
9. Envie o arquivo `.lic` para o cliente por email/WhatsApp

## O cliente ativa a licenca

1. Abre `EditalSystem.exe`
2. Clica em **"Importar Arquivo de Licenca"**
3. Seleciona o `.lic` recebido
4. Pronto — sistema ativado

## Bloquear um cliente (cancelar acesso)

Se voce excluiu o usuario no admin mas o cliente ainda consegue entrar,
e porque a licenca fica salva no computador dele.

Para bloquear definitivamente:

1. Abra o arquivo `blocked_serials.json` na pasta do projeto
2. Adicione o serial key do cliente:
```json
{
  "blocked": ["EDIT-XXXX-XXXX-XXXX"],
  "updated_at": "2026-03-27 10:00:00"
}
```
3. Salve e faca push:
```bash
git add blocked_serials.json
git commit -m "bloqueia serial EDIT-XXXX-XXXX-XXXX"
git push
```
4. Na proxima vez que o cliente abrir o app, ele sera bloqueado
   e precisara de uma nova licenca

## Renovar licenca de um cliente

1. Admin -> Usuarios -> clique no icone **🔄** (renovar)
2. Define quantos dias
3. Exporte novo `.lic` e envie para o cliente

---

# PARTE 6 — ATUALIZAR O APP PARA CLIENTES

Quando voce quiser lancar uma nova versao do app:

## Passo 1 — Atualizar o numero de versao

Abra `client\updater.py` e mude:
```python
APP_VERSION = "1.1.0"  # era 1.0.0
```

## Passo 2 — Gerar novo executavel

Rode o `build.bat` novamente.

## Passo 3 — Criar nova Release no GitHub

1. GitHub -> Releases -> **"Draft a new release"**
2. Tag: `v1.1.0`
3. Titulo: `Edital System v1.1.0`
4. Arraste o arquivo `dist\EditalSystem\` compactado (.zip)
5. Publique

## Passo 4 — Atualizar o version.json

Abra `version.json` e edite:
```json
{
  "version": "1.1.0",
  "download_url": "https://github.com/SEU_USUARIO/edital-system/releases/download/v1.1.0/EditalSystem_v1.1.0.zip",
  "release_notes": "Novos editais adicionados. Correcao de bugs."
}
```

## Passo 5 — Push

```bash
git add .
git commit -m "versao 1.1.0"
git push
```

Da proxima vez que o cliente abrir o app, aparece um popup:
**"Nova versao disponivel! Atualizar agora?"**
Ele clica Sim e baixa automaticamente.

---

# RESUMO DO DIA A DIA

## Quando adicionar/mudar um tutorial:
```
1. Admin -> Editais -> Editar -> cola o link do video -> Salva
2. git add tutorials.json
3. git commit -m "atualiza tutorial X"
4. git push
```

## Quando criar um novo cliente:
```
1. Admin -> Usuarios -> Novo -> preenche -> Salva -> exporta .lic
2. Envia o .lic por email ou WhatsApp
```

## Quando bloquear um cliente:
```
1. Copia o serial key do usuario no admin
2. Adiciona em blocked_serials.json
3. git add blocked_serials.json && git commit -m "bloqueia X" && git push
```

## Quando lancar nova versao:
```
1. Muda APP_VERSION em client/updater.py
2. Roda build.bat
3. Cria Release no GitHub com o .zip
4. Atualiza version.json com link e versao nova
5. git add . && git commit -m "v1.X.X" && git push
```

---

Qualquer duvida, guarde este documento.
