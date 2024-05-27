import csv
import sqlite3
import os
from telethon.sync import TelegramClient, events

# Remember to use your own values from my.telegram.org!
api_id = 'yours'
api_hash = 'yours'
bot_token = 'your_bot_token'
admin_user_id = 'yours'
admin_username = 'yours'
phone_number = 'yours'
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)



def create_or_connect_database(filename='products.db'):
    if os.path.isfile(filename):

        conn = sqlite3.connect(filename)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        expected_columns = ["id", "product_name", "product_code", "price", "is_available"]

        existing_columns = [col[1] for col in columns]
        if existing_columns != expected_columns:
            cursor.execute('''CREATE TABLE IF NOT EXISTS products_new
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               product_name TEXT,
                               product_code TEXT,
                               price BIGINT,
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




@client.on(events.NewMessage())
async def handle_message(event):
    if event.text.lower().startswith('/price'):
        product_query = event.text[7:].strip()  # Extract product query from the message
        cursor.execute('SELECT name, code, price, is_available FROM products WHERE name = ? OR code = ?',
                       (product_query, product_query))
        result = cursor.fetchone()
        if result:
            name, code, price, is_available = result
            if is_available:
                await event.respond(f"Product: {name} (Code: {code})\nPrice: ${price:.2f}")
            else:
                await event.respond(f"{name} is currently unavailable.")
        else:
            await event.respond(f"Product '{product_query}' not found.")



@client.on(events.NewMessage(pattern='./updateproduct'))
async def update_product(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if permissions.is_admin:
            await event.respond("Welcome, administrator!")
        else:
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
                await event.respond("Invalid input. Use /updateproduct <product_id> <column> <value>")
        else:
            await event.respond("You are not authorized to update products.")
    except Exception as e:
        await event.respond(f"Error updating : {str(e)}")




@client.on(events.NewMessage(pattern="./changeavailability"))
async def change_availability(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if permissions.is_admin:
            await event.respond("Welcome, administrator!")
        else:
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
            return await event.respond("Invalid input. Use /changeavailability <product_id> <new_availability>")

        product_id = int(product_id)
        new_availability = new_availability.lower() == "true"

        # Update the 'is_available' field in the 'products' table
        cursor.execute("UPDATE products SET is_available = ? WHERE id = ?", (new_availability, product_id))
        conn.commit()

        await event.respond("Availability updated successfully!")
    except Exception as e:
        await event.respond(f"Error updating availability: {str(e)}")



@client.on(events.NewMessage(pattern="./addproduct"))
async def add_product(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if permissions.is_admin:
            await event.respond("Welcome, administrator!")
        else:
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
            _, name, price, code = message_text.split()
        except ValueError:
            return await event.respond("Invalid input. Use /changeavailability <product_name> <price> <code>")

        true = True

        cursor.execute(f"INSERT INTO products (product_name, product_code, price, is_available) VALUES (?, ?, ?, ?)", (name,code,price,1))
        conn.commit()
        await event.respond(f"add successfully")

    except:
        await event.respond(f"Error adding product")



@client.on(events.NewMessage(pattern="./addproductcsv *\.csv$"))
async def handle_csv(event):
    try:
        permissions = await client.get_permissions(event.sender_id)
        if permissions.is_admin:
            await event.respond("Welcome, administrator!")
        else:
            await event.respond("Sorry, only administrators can access this event.")
            return 0
    except Exception as e:
        await event.respond(f"Error handling event: {str(e)}")

    try:
        file = await event.get_file()
        file_name = file.name

        file_path = f"downloads/{file_name}"
        await file.download_to_drive(file_path)

        # Process the CSV data
        with open(file_path, "r") as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                try:
                    name, price, code , available= row[0], row[1], row[2], row[3]
                    cursor.execute(
                        f"INSERT INTO products (product_name, product_code, price, is_available) VALUES (?, ?, ?, ?)",
                        (name, code, price, available))
                    conn.commit()
                except:
                    await event.respond(f"{row[0]} could not add")
        await event.respond("CSV file received and processed successfully!")
    except Exception as e:
        await event.respond(f"Error handling CSV file: {str(e)}")





if __name__ == '__main__':
    conn = create_or_connect_database()
    cursor = conn.cursor()
    client.start()
    client.run_until_disconnected()
