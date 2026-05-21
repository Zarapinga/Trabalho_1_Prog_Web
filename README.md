# Planejamento Financeiro - Projeto Django

## Descrição do Projeto
Este projeto é uma aplicação web para Controle e Planejamento Financeiro desenvolvida utilizando o framework **Django**. Através desta aplicação, os usuários podem acompanhar suas contas bancárias, registrar receitas e despesas, e realizar simulações de investimentos (como rendimentos para aposentadoria ou compra de um bem).

O projeto atende aos requisitos do Trabalho Prático 1, incluindo a modelagem relacional de banco de dados, painel administrativo protegido e implantação através de containers.

## Funcionalidades Prontas (Checkpoint 1)
- **Modelagem Completa de Banco de Dados**: Tabelas de Perfil, Contas Bancárias, Categorias, Transações e Simulação, conectadas via chaves estrangeiras (`ForeignKey` e `OneToOneField`).
- **Ambiente Administrativo Protegido e Moderno**: Configurado com a biblioteca `django-unfold` e validações de regras de negócios na gestão de finanças diretamente no Admin.
- **Banco de Dados Relacional**: Integrado nativamente com PostgreSQL e com integridade de dados assegurada.
- **Conteinerização com Docker**: Arquitetura padronizada via `docker-compose` e `Dockerfile` abrangendo serviços web (Django) e DB (Postgres).

## Como Executar (Ambiente Docker)

Pré-requisito: É necessário possuir o **Docker** e **Docker Compose** instalados na máquina. O Python e o Banco de Dados serão instalados inteiramente e configurados automaticamente dentro do container!

1. Na raiz do projeto, onde se encontra o arquivo `docker-compose.yml`, construa e suba a imagem:
   ```bash
   docker-compose up --build
   ```
   *(A execução automática criará o banco no postgres, fará o download das dependências e já rodará o comando de migrate).*

2. Em outra aba do terminal (deixe o projeto rodando), crie o usuário administrador para obter acesso total ao sistema:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

3. Acesse o sistema na web abrindo em seu navegador:
   🔗 [http://localhost:8000/admin](http://localhost:8000/admin)

4. Faça o login com os dados de e-mail e senhas criados. Quando finalizar o uso, basta abortar com Ctrl+C no console do servidor e digitar docker-compose down.

## Equipe Desenvolvedora
Desenvolvido colaborativamente no Github.
- _<Raul Soares de Carvalho 202120490>_
- _<Lucas da Silva Rosa 202220235>_

---