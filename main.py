import csv
import sqlite3
import os
from telethon.sync import TelegramClient, events

# Remember to use your own values from my.telegram.org!
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
admin_user_id = os.getenv('ADMIN_USER_ID')
admin_username = os.getenv('ADMIN_USERNAME')
phone_number = os.getenv('PHONE_NUMBER')
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

columns = ["id", "product_name", "product_name_fa", "part_number", "brand", "price_usd",
           "is_available", "region", "product_type", "car_model", "car_brand", "inventory"]


def create_or_connect_database(filename='products.db', expected_columns=columns):
    if os.path.isfile(filename):

        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()

        existing_columns = [col[1] for col in columns]
        if existing_columns != expected_columns:
            cursor.execute('''CREATE TABLE IF NOT EXISTS products_new
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               product_name TEXT,
                               product_name_fa TEXT,
                               part_number TEXT,
                               brand TEXT,
                               region TEXT,
                               product_type TEXT,
                               car_brand,
                               car_model,
                               price_usd BIGINT,
                               inventory BIGINT,
                               is_available BOOLEAN)''')
            cursor.execute("INSERT INTO products_new SELECT * FROM products")
            cursor.execute("DROP TABLE IF EXISTS products")
            cursor.execute("ALTER TABLE products_new RENAME TO products")

        print(f"Connected to existing database: {filename}")
    else:
        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS products
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           product_name TEXT,
                           product_code TEXT,
                           price BIGINT,
                           is_available BOOLEAN)''')
        conn.commit()
        print(f"Created new database: {filename}")

    return conn


# todo
############
# by account#
############


########
# by bot#
########
# @client.on(events.NewMessage())
# async def handle_message(event):
#     if event.text.lower().startswith('/price'):
#         product_query = event.text[7:].strip()  # Extract product query from the message
#         cursor.execute('SELECT name, code, price, is_available FROM products WHERE name = ? OR code = ?',
#                        (product_query, product_query))
#         result = cursor.fetchone()
#         if result:
#             name, code, price, is_available = result
#             if is_available:
#                 await event.respond(f"Product: {name} (Code: {code})\nPrice: ${price:.2f}")
#             else:
#                 await event.respond(f"{name} is currently unavailable.")
#         else:
#             await event.respond(f"Product '{product_query}' not found.")

@client.on(events.NewMessage(pattern='./start'))
async def start_handler(event):
    await event.respond("Welcome! Ask me about a product.")


@client.on(events.NewMessage(pattern='./update_product'))
async def update_product(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if not permissions.is_admin:
            await event.respond("Sorry, only administrators can access this event.")
            return 0
    except Exception as e:
        await event.respond(f"Error handling event: {str(e)}")

    try:
        if event.sender_id == admin_user_id or event.sender_id == phone_number or event.sender_id == admin_username:
            try:
                _, product_id, column, value = event.text.split()
                cursor.execute(f'UPDATE products SET {column} = ? WHERE id = ?', (value, int(product_id)))
                conn.commit()
                await event.respond(f"Product {product_id} updated successfully.")
            except ValueError:
                await event.respond("Invalid input. Use /update_product <product_id> <column> <value>")
        else:
            await event.respond("You are not authorized to update products.")
    except Exception as e:
        await event.respond(f"Error updating : {str(e)}")


@client.on(events.NewMessage(pattern="./change_availability"))
async def change_availability(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if not permissions.is_admin:
            await event.respond("Sorry, only administrators can access this event.")
            return 0
    except Exception as e:
        await event.respond(f"Error handling event: {str(e)}")

    try:
        message_text = event.text.lower()
        if "/changeavailability" not in message_text:
            return
        try:
            _, product_id, new_availability = message_text.split()
        except ValueError:
            return await event.respond("Invalid input. Use /change_availability <product_id> <new_availability>")

        product_id = int(product_id)
        new_availability = new_availability.lower() == "true"

        # Update the 'is_available' field in the 'products' table
        cursor.execute("UPDATE products SET is_available = ? WHERE id = ?", (new_availability, product_id))
        conn.commit()

        await event.respond("Availability updated successfully!")
    except Exception as e:
        await event.respond(f"Error updating availability: {str(e)}")


@client.on(events.NewMessage(pattern="./add_product"))
async def add_product(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if not permissions.is_admin:
            await event.respond("Sorry, only administrators can access this event.")
            return 0
    except Exception as e:
        await event.respond(f"Error handling event: {str(e)}")

    try:
        # Parse the message
        message_text = event.text.lower()
        if "/addproduct" not in message_text:
            return  # Ignore messages that don't match the command

        try:
            message = list(message_text.split())
            if len(message) != 12 or message[0] != "/add_product" or not (message[-3].isnumeric() and message[-2].isnumeric() and message[-1].isnumeric()):
                return await event.respond(
                    "Invalid input. Use /add_product <product_name> <product_name_fa> <part_number> <brand> <region> <product_type> <car_brand> <car_model> <price> <inventory> <is_available>")
        except ValueError:
            return await event.respond("Invalid input. Use /add_product <product_name> <price> <code>")

        cursor.execute('''INSERT INTO products_new
                          (product_name, product_name_fa, part_number, brand, region,
                           product_type, car_brand, car_model, price_usd, inventory, is_available)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (message[1], message[2], message[3], message[4], message[5], message[6], message[7], message[8], int(message[9]), int(message[10]), int(message[11])))
        conn.commit()
        await event.respond(f"add successfully")
    except:
        await event.respond(f"Error adding product")


@client.on(events.NewMessage(pattern=".*\.csv$"))
async def handle_csv(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if not permissions.is_admin:
            await event.respond("Sorry, only administrators can access this event.")
            return 0
    except Exception as e:
        await event.respond(f"Error handling event: {str(e)}")

    try:
        file = await event.get_file()
        file_name = file.name

        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)

        with open(file_path, "r") as csvfile:
            csv_reader = csv.reader(csvfile)
            for message in csv_reader:
                try:
                    cursor.execute('''INSERT INTO products_new
                                      (product_name, product_name_fa, part_number, brand, region,
                                       product_type, car_brand, car_model, price_usd, inventory, is_available)
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                    message[1], message[2], message[3], message[4], message[5], message[6], message[7], message[8],
                    int(message[9]), int(message[10]), int(message[11])))
                    conn.commit()
                    await event.respond(f"add successfully")
                except:
                    await event.respond(f"{message} could not add")
        await event.respond("CSV file received and processed successfully!")
    except Exception as e:
        await event.respond(f"Error handling CSV file: {str(e)}")


if __name__ == '__main__':
    conn = create_or_connect_database('product.db', columns)
    cursor = conn.cursor()
    client.start()
    client.run_until_disconnected()
