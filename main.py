import logging
import telebot
import os
import time
import schedule
from telebot import types
from utils.logger import configure_logger
from services.graphql_client import (
    fetch_inadimplentes_45dias,
    fetch_inadimplentes_30dias,
)
from services.junior_client import get_df_inadimplentes  # Importe a função que criamos

# Obter o logger configurado
logger = configure_logger()

# Obter o token do bot do ambiente
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Obter o ID do Telegram do usuário do ambiente
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

# Variável global para controlar o estado de processamento
is_processing = False
is_routine_running = False

# Verificar se o ID do Telegram do usuário está definido
if not TELEGRAM_USER_ID:
    logger.error(
        "Certifique-se de definir a variável de ambiente TELEGRAM_USER_ID no arquivo .env"
    )
    exit()

# Inicializar o bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


# Verifica se o usuário está autorizado
def is_user_authorized(message):
    user_id = message.from_user.id
    if user_id != int(TELEGRAM_USER_ID):
        logger.warning(f"Usuário não autorizado. ID: {user_id}")
        bot.send_message(user_id, "Você não está autorizado a usar este bot.")
        return False
    return True


# Função para gerar os arquivos e enviar para o Telegram
def generate_and_send_files():
    try:
        # Chama a função para gerar os arquivos Excel
        get_df_inadimplentes()

        # Envia os arquivos gerados para o usuário
        with open("inadimplentes_45_dias.xlsx", "rb") as file_45:
            bot.send_document(TELEGRAM_USER_ID, file_45)
        with open("inadimplentes_30_dias.xlsx", "rb") as file_30:
            bot.send_document(TELEGRAM_USER_ID, file_30)

        bot.send_message(
            TELEGRAM_USER_ID,
            "Os arquivos com os dados de inadimplentes foram gerados com sucesso!",
        )
    except Exception as e:
        logger.error(f"Erro ao gerar arquivos de inadimplentes: {e}")
        bot.send_message(
            TELEGRAM_USER_ID,
            "Ocorreu um erro ao gerar os arquivos. Tente novamente mais tarde.",
        )


# Função para iniciar a rotina de execução diária
def start_daily_routine():
    global is_routine_running
    if not is_routine_running:
        is_routine_running = True
        logger.info("Iniciando rotina diária de inadimplentes.")
        generate_and_send_files()
    else:
        logger.info("A rotina diária já está em execução.")


# Agendar a execução diária às 3 AM
schedule.every().day.at("08:00").do(start_daily_routine)


# Comando /start para exibir uma mensagem inicial com o menu
@bot.message_handler(commands=["start"])
def start(message):
    if not is_user_authorized(message):
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_inadimplentes = types.KeyboardButton("/inadimplentes")
    btn_inadimplentes_excel = types.KeyboardButton("/inadimplentes_excel")
    btn_start_routine = types.KeyboardButton("/start_rotina")  # Novo botão
    btn_stop_routine = types.KeyboardButton("/stop_rotina")  # Novo botão
    markup.add(
        btn_inadimplentes, btn_inadimplentes_excel, btn_start_routine, btn_stop_routine
    )

    bot.send_message(
        message.chat.id,
        "Olá! Bem-vindo ao bot. Escolha uma opção abaixo ou use os comandos:",
        reply_markup=markup,
    )


# Comando /inadimplentes para exibir as quantidades de inadimplentes
@bot.message_handler(commands=["inadimplentes"])
def show_inadimplentes_count(message):
    global is_processing
    if not is_user_authorized(message):
        return

    if is_processing:
        bot.send_message(message.chat.id, "Aguarde, uma operação está em andamento.")
        return

    try:
        # Marcar como processando
        is_processing = True

        # Obtém os dados completos
        data_45 = fetch_inadimplentes_45dias()
        data_30 = fetch_inadimplentes_30dias()

        # Calcula os counts
        count_45 = len(data_45)
        count_30 = len(data_30)

        if data_45 is not None and data_30 is not None:
            bot.send_message(
                message.chat.id,
                f"📊 *Inadimplentes:*\n- 30 dias: {count_30}\n- 45 dias: {count_45}",
                parse_mode="Markdown",
            )
        else:
            bot.send_message(
                message.chat.id,
                "Erro ao buscar dados dos inadimplentes. Tente novamente mais tarde.",
            )
    except Exception as e:
        logger.error(f"Erro ao processar o comando /inadimplentes: {e}")
        bot.send_message(
            message.chat.id, "Ocorreu um erro inesperado. Por favor, tente novamente."
        )
    finally:
        # Desmarcar como processando
        is_processing = False


# Comando /inadimplentes_excel para gerar os arquivos Excel
@bot.message_handler(commands=["inadimplentes_excel"])
def get_inadimplentes_excel(message):
    global is_processing
    if not is_user_authorized(message):
        return

    if is_processing:
        bot.send_message(message.chat.id, "Aguarde, uma operação está em andamento.")
        return

    try:
        # Marcar como processando
        is_processing = True

        # Chama a função para gerar os arquivos Excel
        get_df_inadimplentes()

        # Envia os arquivos gerados para o usuário
        with open("inadimplentes_45_dias.xlsx", "rb") as file_45:
            bot.send_document(message.chat.id, file_45)
        with open("inadimplentes_30_dias.xlsx", "rb") as file_30:
            bot.send_document(message.chat.id, file_30)

        bot.send_message(
            message.chat.id,
            "Os arquivos com os dados de inadimplentes foram gerados com sucesso!",
        )
    except Exception as e:
        logger.error(f"Erro ao gerar arquivos de inadimplentes: {e}")
        bot.send_message(
            message.chat.id,
            "Ocorreu um erro ao gerar os arquivos. Tente novamente mais tarde.",
        )
    finally:
        # Desmarcar como processando
        is_processing = False


# Comando /start_rotina para iniciar a rotina diária
@bot.message_handler(commands=["start_rotina"])
def start_routine(message):
    global is_routine_running
    if not is_user_authorized(message):
        return

    if is_routine_running:
        bot.send_message(message.chat.id, "A rotina diária já está em execução.")
    else:
        is_routine_running = True
        start_daily_routine()
        bot.send_message(message.chat.id, "A rotina diária foi iniciada.")


# Comando /stop_rotina para parar a rotina diária
@bot.message_handler(commands=["stop_rotina"])
def stop_routine(message):
    global is_routine_running
    if not is_user_authorized(message):
        return

    if not is_routine_running:
        bot.send_message(message.chat.id, "A rotina diária não está em execução.")
    else:
        is_routine_running = False
        bot.send_message(message.chat.id, "A rotina diária foi parada.")


# Registrar os comandos no menu do Telegram
bot.set_my_commands(
    [
        types.BotCommand("start", "Iniciar o bot"),
        types.BotCommand("inadimplentes", "Verificar inadimplentes (30 e 45 dias)"),
        types.BotCommand(
            "inadimplentes_excel", "Gerar arquivos Excel de inadimplentes"
        ),
        types.BotCommand("start_rotina", "Iniciar rotina diária de inadimplentes"),
        types.BotCommand("stop_rotina", "Parar rotina diária de inadimplentes"),
    ]
)


# Função principal
def main():
    logger.info("Bot iniciado com sucesso!")
    bot.polling()

    # Loop para manter o agendamento de rotina diária em funcionamento
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
