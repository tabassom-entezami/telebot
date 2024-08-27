import os
import tempfile
import pandas as pd

from telethon.sync import TelegramClient, events
from environs import Env
from dateutil import tz
from telethon import utils

from createdb import PRODUCT_CONN, LOG_CONN


env = Env()
env.read_env()

# Remember to use your own values from my.telegram.org and add it to .env!
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
admin_usernames = list(str(os.getenv('ADMIN_USERNAME')).split())
phone_number = os.getenv('PHONE_NUMBER')
simple_answer_text = os.getenv('SIMPLE_ANSWER_TEXT')
conditional_answer_text = os.getenv('CONDITIONAL_ANSWER_TEXT')

# creating clients
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
user_client = TelegramClient('user_session', api_id, api_hash).start(phone=phone_number)

is_running = False


# if only admins can access use this
def _admin_validator(event):
    return event.is_private and event.sender.username in admin_usernames


def get_bot_chat_id():
    with TelegramClient('bot_session', api_id, api_hash) as bot_client:
        updates = bot_client.get_updates()
        chat_id = updates[0].message.chat.id
    return chat_id


##########
# message#
##########

# update message answering and improve translating
async def handle_message(event):
    chat = await event.get_chat()
    if getattr(chat, 'broadcast', False) or not is_running:
        return
    user = await event.get_sender()

    res = cursor.execute(f'SELECT part_number, is_available, brand, LR FROM products')
    En_to_Fa = str.maketrans(
        {"۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
         " ": "", "?": "", "-": "", "_": "", ".": "", "/": "", "\\": ""})
    chat = str(event.text).translate(En_to_Fa).upper()
    for row in res.fetchall():
        part_number, is_available, brand, lr = row
        if str(part_number).upper() in chat and bool(is_available):
            local_datetime = event.date.astimezone(tz.tzlocal())

            chat_title = utils.get_display_name(await event.get_chat())
            if bool(lr):
                message = conditional_answer_text.format(part_number=part_number, brand=brand).replace('\\n', '\n')
            else:
                message = simple_answer_text.format(part_number=part_number, brand=brand).replace('\\n', '\n')

            #logging
            cursor.execute(
                '''INSERT INTO answerlog
                                          (sender, from_group, part_number, user_message, answer, datetime, LR)
                                          VALUES (?, ?, ?, ?, ?, ?, ?)''', (
                    (user.first_name or '') + ' ' + (user.last_name or ''), chat_title, part_number, event.text, message, local_datetime, lr)
            )
            conn.commit()

            await event.client.send_message(user, message)

#
# async def different_method_handle_message(event):
#     chat = await event.get_chat()
#     if getattr(chat, 'broadcast', False) or getattr(chat, 'status', False) or not is_running:
#         return
#
#     words = event.text.split()
#     words = [i.replace('/', '').replace('-', '').replace('_', '').replace('?', '').replace('.', '') for i in words]
#
#     #part number and name
#     # cursor.execute(f'SELECT product_name, part_number, price_usd, is_available FROM products '
#     #                f'WHERE product_name COLLATE NOCASE IN ({("?," * len(words))[:-1]}) OR '
#     #                f'part_number COLLATE NOCASE IN ({("?," * len(words))[:-1]})',
#     #                (*words, *words))
#
#     # just part number
#     cursor.execute(f'SELECT product_name, part_number, price_usd, is_available, brand FROM products '
#                    f'WHERE part_number COLLATE NOCASE IN ({("?," * len(words))[:-1]})',
#                    words)
#
#     user = await event.get_sender()
#     for row in cursor.fetchall():
#         name, code, price, is_available, brand = row
#         if is_available:
#             await event.client.send_message(user, f"{simple_answer_text}")
#         else:
#             if not_available_test:
#                 await event.client.send_message(user, not_available_test)


client.on(events.NewMessage(incoming=True))(handle_message)
user_client.on(events.NewMessage(incoming=True))(handle_message)


##########
# by bot #
#  ADMIN #
##########

#user client start answering in group
@client.on(events.NewMessage(pattern='/start', incoming=True, func=_admin_validator))
async def start(event):
    global is_running
    is_running = True
    await event.reply('Bot started!')


# user client stop answering in group
@client.on(events.NewMessage(pattern='/stop', incoming=True, func=_admin_validator))
async def stop(event):
    global is_running
    is_running = False
    await event.reply('Bot stopped!')


@client.on(events.NewMessage(pattern='^/welcome$'))
async def welcome(event):
    return await event.respond("Welcome! How can I help you?")


@client.on(events.NewMessage(pattern='^/update_product_value', incoming=True, func=_admin_validator))
async def update_product(event):
    try:
        _, product_id, column, value = event.text.split()

        if _ != "/update_product_value":
            return event.respond("Invalid input. Use /update_product_value <product_id> <column> <value>")

        cursor.execute(f'UPDATE products SET {column} = ? WHERE id = ?', (value, int(product_id)))
        conn.commit()
        return await event.respond(f"Product {product_id} updated successfully.")
    except ValueError:
        return await event.respond("Invalid input. Use /update_product_value <product_id> <column> <value>")


@client.on(events.NewMessage(pattern="^/change_availability", incoming=True, func=_admin_validator))
async def change_availability(event):
    try:
        message_text = event.text.lower()
        if message_text.startswith("/change_availability"):
            return await event.respond("Invalid input. Use /change_availability <product_id> <new_availability>")
        try:
            _, product_id, new_availability = message_text.split()
        except ValueError:
            return await event.respond("Invalid input. Use /change_availability <product_id> <new_availability>")

        product_id = int(product_id)
        new_availability = new_availability.lower() == "true"

        cursor.execute("UPDATE products SET is_available = ? WHERE id = ?", (new_availability, product_id))
        conn.commit()

        return await event.respond("Availability updated successfully!")
    except Exception as e:
        return await event.respond(f"Error updating availability: {str(e)}")


@client.on(events.NewMessage(pattern="^/add_product", incoming=True, func=_admin_validator))
async def add_product(event):
    try:
        message_text = event.text.lower()
        if not message_text.startswith("/add_product"):
            return await event.respond(
                "Invalid input. Use /add_product <product_name> <product_name_fa> <part_number> <brand> <region> <product_type> <car_brand> <car_model> <price> <inventory> <is_available> <LR>"
            )
        try:
            message = list(message_text.split())
            if len(message) != 13 or not (
                    message[-3].isnumeric() and message[-2].isnumeric() and message[-1].isnumeric()):
                return await event.respond(
                    "Invalid input data and be careful about types. Use /add_product <product_name> <product_name_fa> <part_number> <brand> <region> <product_type> <car_brand> <car_model> <price> <inventory> <is_available>"
                )
        except ValueError:
            return await event.respond("Invalid input. Use /add_product <product_name> <price> <code>")

        cursor.execute(
            '''INSERT INTO products
                                      (product_name, product_name_fa, part_number, brand, region,
                                       product_type, car_brand, car_model, price_usd, inventory, is_available, LR)
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                message[1], message[2], message[3], message[4], message[5], message[6], message[7], message[8],
                int(message[9]),
                int(message[10]), int(message[11]), int(message[12]))
        )
        conn.commit()
        await event.respond(f"add successfully")
    except:
        return await event.respond(f"Error adding product")


@client.on(events.NewMessage(incoming=True, func=_admin_validator))
async def handle_csv(event):
    try:
        file = event.file
        if not file:
            return

        if file.mime_type != 'text/csv':
            return

        with tempfile.NamedTemporaryFile() as tmp:
            await event.download_media(tmp.name)
            df = pd.read_csv(tmp.name)
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM SQLITE_SEQUENCE WHERE name='products'")
            conn.commit()
            df.to_sql('products', conn, if_exists='append', index=False)
            return await event.respond("Data imported successfully")
    except Exception as e:
        return await event.respond(f"Error handling CSV file: {str(e)}")


@client.on(events.NewMessage(pattern="^/backup$", incoming=True, func=_admin_validator))
async def backup_handler(event):
    df = pd.read_sql_query("SELECT * FROM products", conn)
    df.to_csv('data.csv', index=False)
    await client.send_file(event.sender.id, 'data.csv')
    os.remove('data.csv')


@client.on(events.NewMessage(pattern="^/log$", incoming=True, func=_admin_validator))
async def log_handler(event):
    df = pd.read_sql_query("SELECT * FROM answerlog", conn)
    df.to_csv('log.csv', index=False)
    await client.send_file(event.sender.id, 'log.csv')
    os.remove('log.csv')


@client.on(events.NewMessage(pattern="^/help$", incoming=True, func=_admin_validator))
async def help_handler(event):
    return await event.respond(
"""All admin commands are:
All commands need to be exact!
in case of adding be careful about data order and type!

**/log** to receive logger file

**/update_product_value** <product_id> <column> <value>  -> to update a product value of specific column

**/change_availability** <product_id> <new_availability> ->to change availability of specific product fast!

**/backup** -> send you a backup csv file from your database.

**/add_product** <product_name> <product_name_fa> <part_number> <brand> <region> <product_type> <car_brand> <car_model> <price> <inventory> <is_available> <LR> -> to add single product

with uploading csv file you can add products to it with order <product_name> <product_name_fa> <part_number> <brand> <region> <product_type> <car_brand> <car_model> <price> <inventory> <is_available> <LR>
""")


if __name__ == '__main__':
    conn = PRODUCT_CONN
    cursor = conn.cursor()
    client.start()
    user_client.start()
    user_client.run_until_disconnected()
    client.run_until_disconnected()
