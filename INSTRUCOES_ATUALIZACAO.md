# Instruções de Atualização para a Versão 2 (Flask)

Siga estes passos para atualizar sua aplicação na VM para a nova versão baseada em Flask.

## 1. Atualizar os Arquivos
Certifique-se de que todos os novos arquivos estejam na VM. Se você usa git:

```bash
git pull origin main
```

Se você transfere arquivos manualmente, certifique-se de copiar:
- `Dockerfile.v2`
- `docker-compose.yml` (o novo, atualizado)
- A pasta `v2_flask/` completa

## 2. Parar a Versão Antiga
Pare o container que está rodando atualmente:

```bash
docker-compose down
```

## 3. Limpar Imagens Antigas (Opcional)
Para liberar espaço, você pode remover a imagem antiga:

```bash
docker rmi klasmel-app:latest
```

## 4. Construir e Iniciar a Nova Versão
Execute o comando abaixo para construir a nova imagem e iniciar o container em segundo plano:

```bash
docker-compose up -d --build
```

## 5. Verificar o Status
Verifique se o container está rodando corretamente:

```bash
docker-compose ps
```
Você deve ver `klasmel_container_v2` com status `Up`.

## 6. Acessar a Aplicação
A nova versão estará rodando na porta **5001**.
Acesse pelo navegador: `http://SEU_IP_DA_VM:5001`

---
**Nota sobre os Dados:**
O mapeamento de volume continua o mesmo (`./:/app`), então seus arquivos Excel na pasta `data/` serão preservados e reconhecidos automaticamente pela nova versão.
