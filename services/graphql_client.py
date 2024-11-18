import requests
import logging
import os

from utils.logger import configure_logger

# Obter o logger configurado
logger = configure_logger()

# URL do endpoint GraphQL
GRAPHQL_URL = os.getenv("GRAPHQL_URL")

# Cabeçalhos para autenticação
HEADERS = {
    "content-type": "application/json",
    "x-hasura-admin-secret": os.getenv("HASURA-SECRET"),
}


# Função para buscar inadimplentes de 45 dias
def fetch_inadimplentes_45dias():
    query = """
    query MyQuery {
        mk01 {
            inadimplentes_45dias {
                codcontrato
                conexao_bloqueada
                esta_reduzida
                ip_comunicacao
                nome_razaosocial
                nome_revenda
                username
            }
        }
    }
    """
    try:
        response = requests.post(GRAPHQL_URL, json={"query": query}, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Retorna o dado completo
        return data.get("data", {}).get("mk01", {}).get("inadimplentes_45dias", [])

    except requests.RequestException as e:
        logger.error(f"Erro ao fazer a requisição GraphQL (45 dias): {e}")
        return []


# Função para buscar inadimplentes de 30 dias
def fetch_inadimplentes_30dias():
    query = """
    query MyQuery {
        mk01 {
            inadimplentes_30dias {
                codcontrato
                conexao_bloqueada
                esta_reduzida
                ip_comunicacao
                nome_razaosocial
                nome_revenda
                username
            }
        }
    }
    """
    try:
        response = requests.post(GRAPHQL_URL, json={"query": query}, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Retorna o dado completo
        return data.get("data", {}).get("mk01", {}).get("inadimplentes_30dias", [])

    except requests.RequestException as e:
        logger.error(f"Erro ao fazer a requisição GraphQL (30 dias): {e}")
        return []
