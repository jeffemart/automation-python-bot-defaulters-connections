import pandas as pd
import requests
import os

from utils.logger import configure_logger
from services.graphql_client import (
    fetch_inadimplentes_45dias,
    fetch_inadimplentes_30dias,
)

# Obter o logger configurado
logger = configure_logger()


def make_request(username, ip_comunicacao):
    url = "https://api.junior.online.dev.br/verificar"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('JUNIOR_AUTH_TOKEN')}",
    }
    data = {"username": username, "bng_ip": ip_comunicacao}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Levanta um erro se o status for 4xx ou 5xx
        return response.json()  # Retorna a resposta como JSON
    except requests.exceptions.HTTPError as errh:
        logger.error(f"Erro HTTP para o username '{username}': {errh}")
        return {}
    except requests.exceptions.RequestException as err:
        logger.error(f"Erro na requisição para o username '{username}': {err}")
        return {}
    except ValueError as e:
        logger.error(
            f"Erro ao tentar converter a resposta para JSON para o username '{username}': {e}"
        )
        return {}


def get_df_inadimplentes():
    try:
        # Obtém os dados completos
        data_45 = fetch_inadimplentes_45dias()
        data_30 = fetch_inadimplentes_30dias()

        if data_45 and data_30:
            # Convertendo os dados para DataFrame
            df_45 = pd.DataFrame(data_45)
            df_30 = pd.DataFrame(data_30)

            # Unificar os DataFrames de 45 e 30 dias sem duplicar os usernames
            df_unificado = pd.concat(
                [
                    df_45[["username", "ip_comunicacao"]],
                    df_30[["username", "ip_comunicacao"]],
                ]
            )
            df_unificado.drop_duplicates(
                subset=["username"], keep="first", inplace=True
            )

            # Lista para armazenar as respostas
            responses = {}

            # Requisições para os usernames únicos
            for i in range(len(df_unificado)):
                username = df_unificado.iloc[i]["username"]
                ip_comunicacao = df_unificado.iloc[i]["ip_comunicacao"]

                # Evita duplicação de consulta
                if username not in responses:
                    response = make_request(username, ip_comunicacao)
                    responses[username] = response
                else:
                    response = responses[username]

                # Adiciona status e plano aos DataFrames originais
                if "status" in response:
                    status = response["status"]
                    plano = response.get("plano", "Desconhecido")
                    df_45.loc[df_45["username"] == username, "status"] = status
                    df_45.loc[df_45["username"] == username, "plano"] = plano
                    df_30.loc[df_30["username"] == username, "status"] = status
                    df_30.loc[df_30["username"] == username, "plano"] = plano

            # Salvando os DataFrames em arquivos Excel separados
            with pd.ExcelWriter("inadimplentes_45_dias.xlsx") as writer:
                df_45.to_excel(writer, sheet_name="Inadimplentes_45_dias", index=False)

            with pd.ExcelWriter("inadimplentes_30_dias.xlsx") as writer:
                df_30.to_excel(writer, sheet_name="Inadimplentes_30_dias", index=False)

            logger.info("Arquivos Excel gerados com sucesso!")
        else:
            logger.error("Não foi possível obter os dados dos inadimplentes.")

    except Exception as e:
        logger.error(f"Erro ao obter ou processar os dados: {e}")
