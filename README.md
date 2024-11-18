# Telegram Bot para Gerenciamento de Inadimplentes

Este projeto é um bot do Telegram para gerenciar inadimplentes, desenvolvido em Python. Ele permite visualizar a quantidade de inadimplentes em períodos de 30 e 45 dias e gerar relatórios em formato Excel diretamente pelo Telegram.

## Funcionalidades

- **/start**: Exibe um menu inicial com as opções disponíveis.
- **/inadimplentes**: Retorna o número de inadimplentes em períodos de 30 e 45 dias.
- **/inadimplentes_excel**: Gera e envia relatórios Excel com os inadimplentes de 30 e 45 dias.

## Pré-requisitos

- Python 3.8 ou superior
- Bibliotecas necessárias listadas no arquivo `requirements.txt`
- Um bot Telegram configurado (obtenha o token pelo BotFather)
- Docker instalado para executar a aplicação com variáveis de ambiente configuradas.

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
