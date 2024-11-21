import logging


def configure_logger():
    # Configura o logger principal
    logger = logging.getLogger()

    # Verificar se o logger já foi configurado (para evitar configurações duplicadas)
    if not logger.hasHandlers():
        # Configura o arquivo de log
        file_handler = logging.FileHandler("app.log")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Adiciona o manipulador do arquivo ao logger
        logger.addHandler(file_handler)

        # Configura o console para exibir apenas logs de erro
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

        # Define o nível do logger para capturar logs de INFO e acima
        logger.setLevel(logging.INFO)

    return logger
