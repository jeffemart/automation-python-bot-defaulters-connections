import logging
import telebot
import os
import time
import schedule
import threading
from telebot import types
from utils.logger import configure_logger
from services.graphql_client import (
    fetch_inadimplentes_45dias,
    fetch_inadimplentes_30dias,
)
from services.junior_client import get_df_inadimplentes  # Importe a função que criamos

# Configurar o logger
logger = configure_logger()

# Obter o token do bot e o ID do usuário do ambiente
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

if not TELEGRAM_BOT_TOKEN:
    logger.error("Defina a variável TELEGRAM_BOT_TOKEN no arquivo .env")
    exit()

if not TELEGRAM_USER_ID:
    logger.error("Defina a variável TELEGRAM_USER_ID no arquivo .env")
    exit()

# Inicializar o bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Controle de estados com uma classe
class BotState:
    def __init__(self):
        self.is_processing = False
        self.is_routine_running = False

state = BotState()

# Verifica se o usuário está autorizado
def is_user_authorized(message):
    user_id = message.from_user.id
    if user_id != int(TELEGRAM_USER_ID):
        logger.warning(f"Usuário não autorizado tentou acesso. ID: {user_id}")
        return False
    return True

# Função para gerar os arquivos e enviar para o Telegram
def generate_and_send_files():
    try:
        logger.info("🔄 Iniciando a geração dos arquivos de inadimplentes.")
        get_df_inadimplentes()

        # Verifica se os arquivos foram criados
        if not os.path.exists("inadimplentes_45_dias.xlsx") or not os.path.exists(
            "inadimplentes_30_dias.xlsx"
        ):
            raise FileNotFoundError("Arquivos de inadimplentes não foram gerados.")

        # Envia os arquivos gerados para o usuário
        logger.info("📤 Enviando os arquivos gerados para o usuário.")
        with open("inadimplentes_45_dias.xlsx", "rb") as file_45:
            bot.send_document(TELEGRAM_USER_ID, file_45)
        with open("inadimplentes_30_dias.xlsx", "rb") as file_30:
            bot.send_document(TELEGRAM_USER_ID, file_30)

        bot.send_message(
            TELEGRAM_USER_ID,
            "Os arquivos com os dados de inadimplentes foram gerados e enviados com sucesso!",
        )
        logger.info("✅ Arquivos enviados com sucesso.")

        # Remover os arquivos gerados para economizar espaço
        os.remove("inadimplentes_45_dias.xlsx")
        os.remove("inadimplentes_30_dias.xlsx")
    except Exception as e:
        logger.error(f"Erro ao gerar ou enviar arquivos: {e}")
        bot.send_message(
            TELEGRAM_USER_ID,
            "Ocorreu um erro ao gerar ou enviar os arquivos. Verifique os logs.",
        )

# Função para iniciar a rotina de execução
def start_daily_routine():
    if state.is_routine_running:
        logger.info("⚠️  Rotina diária já está em execução.")
        return

    state.is_routine_running = True
    logger.info("🚀 Iniciando a rotina diária.")
    try:
        generate_and_send_files()
    except Exception as e:
        logger.error(f"Erro na rotina diária: {e}")
    finally:
        state.is_routine_running = False
        logger.info("✅ Rotina diária concluída.")

# Função para parar a rotina de execução
def stop_daily_routine():
    # Para interromper a execução, podemos forçar o agendamento a ser ignorado
    logger.info("🛑 Tentando parar a rotina diária.")
    state.is_routine_running = False
    # Desmarcar a próxima execução agendada:
    schedule.clear()  # Limpa todos os agendamentos
    logger.info("✅ Rotina diária foi parada e os agendamentos foram limpos.")

# Agendar a execução 
schedule.every().day.at("08:00").do(start_daily_routine)


# Handlers de comandos
@bot.message_handler(commands=["start"])
def start(message):
    if not is_user_authorized(message):
        bot.send_message(message.chat.id, "Você não está autorizado a usar este bot.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("/inadimplentes"),
        types.KeyboardButton("/inadimplentes_excel"),
        types.KeyboardButton("/start_rotina"),
        types.KeyboardButton("/stop_rotina"),
    )

    bot.send_message(
        message.chat.id,
        "Olá! Bem-vindo ao bot. Escolha uma opção abaixo ou use os comandos:",
        reply_markup=markup,
    )

@bot.message_handler(commands=["inadimplentes"])
def show_inadimplentes_count(message):
    if not is_user_authorized(message):
        bot.send_message(message.chat.id, "Você não está autorizado a usar este bot.")
        return

    if state.is_processing:
        bot.send_message(message.chat.id, "Aguarde, uma operação está em andamento.")
        return

    try:
        state.is_processing = True
        data_45 = fetch_inadimplentes_45dias()
        data_30 = fetch_inadimplentes_30dias()

        count_45 = len(data_45)
        count_30 = len(data_30)

        bot.send_message(
            message.chat.id,
            f"📊 *Inadimplentes:*\n- 30 dias: {count_30}\n- 45 dias: {count_45}",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Erro ao processar o comando /inadimplentes: {e}")
        bot.send_message(
            message.chat.id, "Ocorreu um erro inesperado. Por favor, tente novamente."
        )
    finally:
        state.is_processing = False

@bot.message_handler(commands=["inadimplentes_excel"])
def get_inadimplentes_excel(message):
    if not is_user_authorized(message):
        bot.send_message(message.chat.id, "Você não está autorizado a usar este bot.")
        return

    if state.is_processing:
        bot.send_message(message.chat.id, "Aguarde, uma operação está em andamento.")
        return

    try:
        state.is_processing = True
        generate_and_send_files()
    except Exception as e:
        logger.error(f"Erro ao processar o comando /inadimplentes_excel: {e}")
        bot.send_message(
            message.chat.id,
            "Ocorreu um erro ao gerar os arquivos. Tente novamente mais tarde.",
        )
    finally:
        state.is_processing = False

@bot.message_handler(commands=["start_rotina"])
def start_routine(message):
    if not is_user_authorized(message):
        bot.send_message(message.chat.id, "Você não está autorizado a usar este bot.")
        return

    if state.is_routine_running:
        bot.send_message(message.chat.id, "A rotina diária já está em execução.")
    else:
        start_daily_routine()
        bot.send_message(message.chat.id, "A rotina diária foi iniciada.")

@bot.message_handler(commands=["stop_rotina"])
def stop_routine(message):
    if not is_user_authorized(message):
        bot.send_message(message.chat.id, "Você não está autorizado a usar este bot.")
        return

    stop_daily_routine()
    bot.send_message(message.chat.id, "A rotina diária foi parada.")

# Função principal
def start_bot():
    logger.info("🤖 Bot iniciado com sucesso!")
    try:
        bot.polling(none_stop=True)
        logger.info("💬 Bot de Telegram pronto para receber comandos.")
    except Exception as e:
        logger.error(f"Erro ao iniciar o bot de Telegram: {e}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    while True:
        try:
            schedule.run_pending()
            time.sleep(10)
        except Exception as e:
            logger.error(f"Erro no loop de agendamento: {e}")
