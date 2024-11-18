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
        "authority": "junior.online.dev.br",
        "accept": "application/json, text/plain, */*",
        "accept-language": "pt-BR,pt;q=0.9",
        "cache-control": "no-cache",
        "cookie": "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d=eyJpdiI6IjlNV1hlTVNRVnByNXU1Q3ZOb09DOEE9PSIsInZhbHVlIjoiTlp1M0pMOWFtMStEMzNVOGU2MkZFRzhneG10bHZWaWsxbzN2cnprS2t6VG1BOVlzYTdteU9OZERzNFAxc0tha2tybGtkS3dId2xJc2M2VG5mWXNsUzhzYzE1SE9qTFMxTnQxbnZVdkg2SUR0TERCY3Z1RnBCeTBPNHIzZ1dEWHZHR2t1amt3eWtBYzc1OCszWWJVTWNmUnE4SDZhVHlRU3J2bmMzMmRRRFEwcTBzZGR4WHZ0amdhYmgzak5zRmJYak4xb0I2UEI4aHZ3M1RrcXBJcFJVbExmaVR1QkZOVVFXd2ttU083YVZ6UT0iLCJtYWMiOiIyM2UxYjE4Yzk5ZTE0N2NmMDZiNDdhM2NhMzIwZmU4N2RlYTdjYzY5ZDIwMjk4ZjdkYzFkNDI4NDVmNzA4NDM5IiwidGFnIjoiIn0%3D; XSRF-TOKEN=eyJpdiI6IjdwNE45UFE4TVA1V0c4d0ZqM2Q2MFE9PSIsInZhbHVlIjoiYlVBcVRoS3E1bng2N2p6cHo3eWVtOURDNlF5eUdLMkR2bWhNUGZzd1hQZWxNSEk2eXZjck5Na0N0akJmSFB1V2VQcnZaR1pheTVYd0JzRm41bkI4TCtpRnlkMzF6bzdQV3gyUkZCK1pOU0dDd0RsMTNBQ3BpVUtvSVIyTEl2NWEiLCJtYWMiOiI1MTJjY2U1N2ZiNmQ1OWVkZDMwNmNiMzk0OTZhM2QyY2RjZjU4OWJhZTRmMzA3NmNhZDNkZWRhM2ZhYzM4YjRiIiwidGFnIjoiIn0%3D; junior_session=eyJpdiI6IitZaUR3WE5VTGRHNzZCVlV4d0JBZmc9PSIsInZhbHVlIjoiNTcvajVWQU5HQkFjVFNxL2c2U1l1UW0xK3BuaTgrVWE2UWlleG8vMmxuZUczdjZxSG0zZlJPT0tyZ3RqL3orZ3NWa3kvdHB3OU50ZXArcHVzSTEyckhrSm1PU1lPR0t1QVFpWGtCaVdmY21kTWJlU3l6cDIwYjFQa2dtQlQ4R1YiLCJtYWMiOiI5M2ZlYzhjN2EzNjY0ZmVmYjk0MzFiNWIyNzRlODE2MjY5MTcyZThhZTkzYmE4NTg3MzhjODdmMWJmODFjMzVkIiwidGFnIjoiIn0%3D",
        "pragma": "no-cache",
        "referer": "https://junior.online.dev.br/home",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "token": os.getenv("JUNIOR_API_TOKEN"),
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36",
        "x-xsrf-token": os.getenv("JUNIOR_XSRF_TOKEN"),
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
