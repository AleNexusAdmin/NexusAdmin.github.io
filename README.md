# NexusAdmin.github.io

## IA simples com interface de conversa e envio de arquivos

Agora o projeto tem uma interface web para conversar com a IA e enviar arquivos de texto para ela aprender.

### O que essa IA faz

- responde **somente** usando informações fornecidas por você;
- aprende continuamente com mensagens do chat;
- aprende também com o conteúdo de arquivos enviados;
- salva memória em `memoria_usuario.json`.

## Como rodar

1. Execute o servidor:

```bash
python3 web_chat.py
```

2. Abra no navegador:

```text
http://127.0.0.1:5000
```

## Endpoints da interface

- `POST /api/message` → envia mensagem de chat
- `POST /api/upload` → envia arquivo para aprendizado
- `POST /api/clear` → limpa toda memória

## Arquivos principais

- `chatbot_memoria.py` → motor de memória e recuperação de contexto
- `web_chat.py` → API + interface web (sem dependências externas)
- `templates/index.html` → tela de chat e upload


## Gerar ZIP para download (sem versionar binários)

Para manter compatibilidade do repositório, o arquivo ZIP **não é commitado**.
Gere localmente quando precisar:

```bash
./gerar_zip.sh
```
