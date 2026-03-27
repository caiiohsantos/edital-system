# 🚦 Edital System — Documentação Completa

Sistema profissional de consulta de editais com controle de licenças, painel administrativo e interface moderna.

---

## 📁 Estrutura do Projeto

```
edital_system/
├── core/
│   ├── editals_data.py     # Dados de todos os editais (P1-P4)
│   ├── database.py         # Banco de dados (Admin + Cliente)
│   ├── utils.py            # Utilitários (IP, MAC, serial key, YouTube)
│   └── license_core.py     # Sistema de licenças (geração + validação)
├── admin/
│   └── painel_admin.py     # Painel administrativo completo
├── client/
│   ├── app.py              # Aplicativo cliente (usuário final)
│   └── updater.py          # Sistema de auto-update
├── assets/
│   └── icon.ico            # Ícone do aplicativo (você deve criar)
├── requirements.txt
├── build_client.spec       # PyInstaller — cliente
├── build_admin.spec        # PyInstaller — admin
├── edital_system.iss       # Script Inno Setup — instalador Windows
└── README.md
```

---

## ⚡ Instalação Rápida (Desenvolvimento)

```bash
# 1. Clone/extraia o projeto
cd edital_system

# 2. Crie ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
# ou: source venv/bin/activate  # Linux/Mac

# 3. Instale dependências
pip install PySide6 PySide6-WebEngine requests pyinstaller

# 4. Rode o painel admin (senha padrão: admin123)
python admin/painel_admin.py

# 5. Rode o cliente
python client/app.py
```

---

## 🔐 Sistema de Licenças

### Fluxo completo:

```
Admin cria usuário → Gera serial key → Exporta arquivo .lic
         ↓
Cliente recebe o .lic → Importa no app → Licença ativada
         ↓
MAC address é vinculado na primeira ativação
         ↓
Cada vez que o cliente abre: valida assinatura + data + MAC
```

### No Painel Admin:
1. Acesse a aba **Usuários**
2. Clique em **+ Novo Usuário**
3. Preencha nome, e-mail, defina os dias de validade
4. Clique em **Gerar** para criar o serial key
5. Salve o usuário
6. Clique em **📄** (exportar licença) para gerar o arquivo `.lic`
7. Envie o `.lic` para o usuário

### No App Cliente:
1. Ao abrir, clique em **Importar Arquivo de Licença**
2. Selecione o `.lic` recebido
3. O sistema valida e ativa automaticamente

---

## 🎥 Tutoriais YouTube

### Configurar tutorial:
1. No Admin → aba **Editais / Tutoriais**
2. Clique em **✏️ Editar** no edital desejado
3. Cole o link do YouTube (ex: `https://youtu.be/XXXXXXXXXXX`)
4. Salve

### Distribuir para clientes:
Os tutoriais ficam salvos no banco do admin. Para atualizar os clientes, você tem 3 opções:
- **Opção A**: Re-exportar o `.lic` e incluir um arquivo `tutorials.json` junto
- **Opção B**: Implementar API REST (ver seção API abaixo)
- **Opção C**: Distribuir atualização do app com os novos URLs embutidos

---

## 🔄 Auto-Update

O sistema de update verifica uma URL remota com JSON no formato:

```json
{
  "version": "1.1.0",
  "download_url": "https://seusite.com.br/EditalSystem_v1.1.0_Setup.exe",
  "release_notes": "Novos editais adicionados. Melhorias de performance.",
  "min_version": "1.0.0"
}
```

### Configurar:
1. Admin → **Configurações**
2. Informe a URL de atualização (pode ser GitHub Raw, Dropbox, servidor próprio, etc.)
3. Salve

### Como hospedar o JSON (opções gratuitas):
- **GitHub**: Crie um repositório e use a URL raw do arquivo
- **GitHub Gist**: Cole o JSON em um Gist público
- **Dropbox**: Compartilhe o arquivo com link direto

---

## 📦 Build — Criar Executável

### Pré-requisitos:
```bash
pip install pyinstaller
```

### 1. Build do Cliente:
```bash
pyinstaller build_client.spec --clean
# Executável em: dist/client/EditalSystem.exe
```

### 2. Build do Admin:
```bash
pyinstaller build_admin.spec --clean
# Executável em: dist/admin_build/EditalAdmin.exe
```

### 3. Criar Instalador Windows (Inno Setup):
1. Baixe e instale o [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Abra o arquivo `edital_system.iss`
3. Compile: **Build → Compile** (ou F9)
4. Instalador gerado em: `dist/installer/EditalSystem_Setup_v1.0.0.exe`

---

## 🖥️ Interface — Visão Geral

### Painel Admin:
- **Dashboard**: Estatísticas (total, ativos, vencendo, expirados)
- **Usuários**: CRUD completo, exportar licença, bloquear/ativar, renovar
- **Editais**: Configurar URL do tutorial YouTube para cada edital
- **Configurações**: Alterar senha, definir versão e URL de update

### App Cliente:
- **Tela de Ativação**: Importar arquivo `.lic`
- **Tela Principal**: Cards organizados por prioridade (🔴🟡🔵⚪)
- **Filtros**: Busca por texto + filtro por prioridade
- **Status**: 🟢 Verificado / 🔴 Não verificado (com data/hora)
- **Botões por card**:
  - 📋 Edital → abre link do edital no navegador (marca como verificado)
  - 🔍 Consulta → abre link de consulta no navegador (marca como verificado)
  - ▶ Tutorial → abre YouTube dentro do app (QWebEngineView)
- **Auto-update**: Verifica ao abrir

---

## ⚙️ Configurações Avançadas

### Alterar senha padrão do admin:
A senha padrão é `admin123`. Altere na primeira execução em:
Admin → Configurações → Alterar Senha

### Banco de dados Admin:
Localização: `admin/users.db` (SQLite)
- Faça backup regularmente
- Não compartilhe com clientes

### Banco de dados Cliente:
Localização (Windows): `%LOCALAPPDATA%\EditalSystem\client.db`
Localização (Linux/Mac): `~/.edital_system/client.db`

---

## 🛡️ Segurança

| Recurso | Status |
|---------|--------|
| Senha admin com hash SHA-256 | ✅ |
| Licenças assinadas com HMAC-SHA256 | ✅ |
| MAC address vinculado à licença | ✅ |
| Validação de data de expiração | ✅ |
| Banco do admin separado do cliente | ✅ |
| Ofuscação via PyInstaller | ✅ |

### Para produção, recomende também:
- Usar **PyArmor** para ofuscação adicional do código
- Armazenar a chave secreta do HMAC em variável de ambiente ou HSM
- Implementar validação online via API (HTTPS) para maior segurança

---

## 🐛 Troubleshooting

**"QWebEngineView não disponível"**
```bash
pip install PySide6-WebEngine
```

**"Licença vinculada a outro dispositivo"**
- No admin, localize o usuário e clique em 📄 para gerar nova licença
- A nova licença terá o campo MAC em branco (será vinculada no primeiro uso)

**Build falha com erro de imports**
```bash
# Certifique-se que está na pasta raiz do projeto
cd edital_system
pyinstaller build_client.spec --clean --noconfirm
```

**Admin não abre o banco**
- O banco `admin/users.db` é criado automaticamente na primeira execução
- Verifique permissão de escrita na pasta

---

## 📞 Suporte

Desenvolvido por Felipe — 2026
