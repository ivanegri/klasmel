# Klasmel - Sistema de Gestão de Estoque

Este é um sistema de gestão de estoque e produção desenvolvido em Streamlit.

## Estrutura do Projeto

- `Home.py`: Página principal da aplicação.
- `pages/`: Contém as páginas de Contagem e Relatórios.
- `Base_estoque.xlsx`: Arquivo base com os produtos e estoque mínimo.
- `Dockerfile`: Arquivo para criar a imagem Docker.
- `docker-compose.yml`: Arquivo para orquestrar o container.

## Como Rodar Localmente

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute a aplicação:
   ```bash
   streamlit run Home.py
   ```

## Como Rodar com Docker

1. Construa a imagem:
   ```bash
   docker build -t klasmel-app .
   ```
2. Execute o container:
   ```bash
   docker run -p 8501:8501 -v $(pwd):/app klasmel-app
   ```

## Como Rodar com Docker Compose

```bash
docker-compose up -d
```

## Publicando no GitHub e Docker Hub

1. Crie um repositório no GitHub.
2. Siga as instruções para enviar o código.
3. Crie uma conta no Docker Hub.
4. Faça login no terminal: `docker login`
5. Tag a imagem: `docker tag klasmel-app seu-usuario/klasmel-app:latest`
6. Envie a imagem: `docker push seu-usuario/klasmel-app:latest`

## Rodando na VM

1. Copie o `docker-compose.yml` para a VM.
2. Ajuste a imagem no `docker-compose.yml` para `seu-usuario/klasmel-app:latest`.
3. Execute `docker-compose up -d`.
