import mysql.connector
import datetime
def connect_db():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',
            database='credit_card_management'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def create_tables():
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'user') NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Cards (
                    card_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    card_type ENUM('Premium', 'Gold', 'Silver') NOT NULL,
                    balance DECIMAL(10, 2) DEFAULT 0.00,
                    expiry_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Transactions (
                    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                    card_id INT,
                    amount DECIMAL(10, 2) NOT NULL,
                    transaction_type ENUM('Credit', 'Debit') NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (card_id) REFERENCES Cards(card_id) ON DELETE CASCADE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ActivityLogs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    action VARCHAR(255) NOT NULL,
                    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS CardRequests (
                    request_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    card_id INT,
                    request_type ENUM('Delete', 'Upgrade') NOT NULL,
                    new_card_type ENUM('Premium', 'Gold', 'Silver') DEFAULT NULL,
                    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('Pending', 'Accepted', 'Denied') DEFAULT 'Pending',
                    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (card_id) REFERENCES Cards(card_id) ON DELETE CASCADE
                );
            """)
            connection.commit()
            print("Tables created successfully.")
        except mysql.connector.Error as err:
            print(f"Error creating tables: {err}")
        finally:
            cursor.close()
            connection.close()

def register_user(username, password, role):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM Users WHERE username=%s", (username,))
            user_exists = cursor.fetchone()
            if user_exists:
                print("Error registering user: Username already exists.")
                return

            cursor.execute(
                "INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )
            connection.commit()
            print("User registered successfully.")
        except mysql.connector.Error as err:
            print(f"Error registering user: {err}")
        finally:
            cursor.close()
            connection.close()

def log_activity(user_id, action):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO ActivityLogs (user_id, action) VALUES (%s, %s)",
                (user_id, action)
            )
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error logging activity: {err}")
        finally:
            cursor.close()
            connection.close()

def login():
    username = input("Enter username: ")
    password = input("Enter password: ")
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM Users WHERE username=%s AND password=%s",
                (username, password)
            )
            user = cursor.fetchone()
            if user:
                print("Login successful.")
                return user
            else:
                print("Invalid username or password.")
        except mysql.connector.Error as err:
            print(f"Error during login: {err}")
        finally:
            cursor.close()
            connection.close()
    return None

def create_card(user_id, card_type):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            expiry_date = datetime.date.today() + datetime.timedelta(days=365 * 3)  # 3 years from today
            cursor.execute(
                "INSERT INTO Cards (user_id, card_type, expiry_date) VALUES (%s, %s, %s)",
                (user_id, card_type, expiry_date)
            )
            connection.commit()
            log_activity(user_id, f"Created a {card_type} card.")
            print("Card created successfully.")
        except mysql.connector.Error as err:
            print(f"Error creating card: {err}")
        finally:
            cursor.close()
            connection.close()

def delete_card(card_id, user_id):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM Cards WHERE card_id=%s", (card_id,))
            connection.commit()
            log_activity(user_id, "Deleted a card.")
            print("Card deleted successfully.")
        except mysql.connector.Error as err:
            print(f"Error deleting card: {err}")
        finally:
            cursor.close()
            connection.close()

def upgrade_card(card_id, new_type, user_id):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE Cards SET card_type=%s WHERE card_id=%s",
                (new_type, card_id)
            )
            connection.commit()
            log_activity(user_id, f"Upgraded card {card_id} to {new_type}.")
            print("Card upgraded successfully.")
        except mysql.connector.Error as err:
            print(f"Error upgrading card: {err}")
        finally:
            cursor.close()
            connection.close()

def view_cards(user_id):
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Cards WHERE user_id=%s", (user_id,))
            cards = cursor.fetchall()
            return cards
        except mysql.connector.Error as err:
            print(f"Error viewing cards: {err}")
        finally:
            cursor.close()
            connection.close()
    return []

def add_transaction(card_id, amount, transaction_type, user_id):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            if transaction_type == 'Debit':
                cursor.execute("SELECT balance FROM Cards WHERE card_id=%s", (card_id,))
                current_balance = cursor.fetchone()[0]
                if current_balance < amount:
                    print("Insufficient balance.")
                    return
                cursor.execute(
                    "UPDATE Cards SET balance = balance - %s WHERE card_id = %s",
                    (amount, card_id)
                )
            elif transaction_type == 'Credit':
                cursor.execute(
                    "UPDATE Cards SET balance = balance + %s WHERE card_id = %s",
                    (amount, card_id)
                )
            cursor.execute(
                "INSERT INTO Transactions (card_id, amount, transaction_type) VALUES (%s, %s, %s)",
                (card_id, amount, transaction_type)
            )
            connection.commit()
            log_activity(user_id, f"{transaction_type} of amount {amount} on card {card_id}.")
            print("Transaction successful.")
        except mysql.connector.Error as err:
            print(f"Error adding transaction: {err}")
        finally:
            cursor.close()
            connection.close()

def view_transactions(card_id):
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Transactions WHERE card_id=%s", (card_id,))
            transactions = cursor.fetchall()
            return transactions
        except mysql.connector.Error as err:
            print(f"Error viewing transactions: {err}")
        finally:
            cursor.close()
            connection.close()
    return []

def view_activity_logs():
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM ActivityLogs")
            logs = cursor.fetchall()
            for log in logs:
                print(log)
        except mysql.connector.Error as err:
            print(f"Error fetching activity logs: {err}")
        finally:
            cursor.close()
            connection.close()
def send_card_request(user_id, card_id, request_type, new_card_type=None):
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO CardRequests (user_id, card_id, request_type, new_card_type) VALUES (%s, %s, %s, %s)",
                (user_id, card_id, request_type, new_card_type)
            )
            connection.commit()
            print(f"Request for {request_type} sent successfully.")
        except mysql.connector.Error as err:
            print(f"Error sending request: {err}")
        finally:
            cursor.close()
            connection.close()
def process_card_request():
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM CardRequests WHERE status = 'Pending'")
            requests = cursor.fetchall()
            if not requests:
                print("No pending card requests to process.")
                return

            print("Pending Card Requests:")
            for request in requests:
                print(request)

            request_id = input("Enter the ID of the request to process: ")
            cursor.execute("SELECT * FROM CardRequests WHERE request_id = %s", (request_id,))
            request = cursor.fetchone()

            if not request:
                print("Request not found.")
                return

            action = input("Enter action (Accept/Deny): ").strip().lower()
            if action == 'accept':
                if request['request_type'] == 'Delete':
                    cursor.execute("DELETE FROM Cards WHERE card_id = %s", (request['card_id'],))
                    print(f"Card ID {request['card_id']} deleted successfully.")
                elif request['request_type'] == 'Upgrade':
                    cursor.execute(
                        "UPDATE Cards SET card_type = %s WHERE card_id = %s",
                        (request['new_card_type'], request['card_id'])
                    )
                    print(f"Card ID {request['card_id']} upgraded to {request['new_card_type']}.")
                cursor.execute("UPDATE CardRequests SET status = 'Accepted' WHERE request_id = %s", (request_id,))
                print("Request accepted.")
            elif action == 'deny':
                cursor.execute("UPDATE CardRequests SET status = 'Denied' WHERE request_id = %s", (request_id,))
                print("Request denied.")
            else:
                print("Invalid action.")
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error processing card request: {err}")
        finally:
            cursor.close()
            connection.close()

def view_card_requests():
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM CardRequests WHERE status = 'Pending'")
            requests = cursor.fetchall()
            for request in requests:
                print(request)
        except mysql.connector.Error as err:
            print(f"Error viewing card requests: {err}")
        finally:
            cursor.close()
            connection.close()

def view_all_cards():
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Cards")
            cards = cursor.fetchall()
            if cards:
                print("All Cards:")
                for card in cards:
                    print(card)
            else:
                print("No cards found.")
        except mysql.connector.Error as err:
            print(f"Error fetching all cards: {err}")
        finally:
            cursor.close()
            connection.close()

def view_all_transactions():
    connection = connect_db()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM Transactions")
            transactions = cursor.fetchall()
            if transactions:
                print("All Transactions:")
                for transaction in transactions:
                    print(transaction)
            else:
                print("No transactions found.")
        except mysql.connector.Error as err:
            print(f"Error fetching all transactions: {err}")
        finally:
            cursor.close()
            connection.close()


def admin_menu(user):
    while True:
        print("\nAdmin Menu")
        print("1. Register User")
        print("2. View All Cards")
        print("3. View All Transactions")
        print("4. View Activity Logs")
        print("5. View Card Requests")
        print("6. Process Card Requests")
        print("7. Add Transactions")
        print("8. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            role = input("Enter role (admin/user): ")
            register_user(username, password, role)
        elif choice == '2':
            view_all_cards()
        elif choice == '3':
            view_all_transactions()
        elif choice == '4':
            view_activity_logs()
        elif choice == '5':
            view_card_requests()
        elif choice == '6':
            process_card_request()
        elif choice=='7':
            card_id = int(input("Enter card ID for transaction: "))
            amount = float(input("Enter transaction amount: "))
            transaction_type = input("Enter transaction type (Credit/Debit): ")
            if transaction_type in ['Credit', 'Debit']:
                add_transaction(card_id, amount, transaction_type, user['user_id'])
            else:
                print("Invalid transaction type.")
        elif choice == '8':
            break
        else:
            print("Invalid choice.")


def user_menu(user):
    while True:
        print("\nUser Menu")
        print("1. Create Card")
        print("2. View My Cards")
        print("3. Request Card Deletion")
        print("4. Request Card Upgrade")
        print("5. Add Transaction")
        print("6. View Transactions")
        print("7. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            print("Card Types: Premium, Gold, Silver")
            card_type = input("Enter card type: ")
            if card_type in ['Premium', 'Gold', 'Silver']:
                create_card(user['user_id'], card_type)
            else:
                print("Invalid card type.")
        elif choice == '2':
            cards = view_cards(user['user_id'])
            for card in cards:
                print(card)
        elif choice == '3':
            card_id = int(input("Enter card ID to request deletion: "))
            send_card_request(user['user_id'], card_id, 'Delete')
        elif choice == '4':
            card_id = int(input("Enter card ID to request upgrade: "))
            new_type = input("Enter new card type (Premium, Gold, Silver): ")
            if new_type in ['Premium', 'Gold', 'Silver']:
                send_card_request(user['user_id'], card_id, 'Upgrade', new_type)
            else:
                print("Invalid card type.")
        elif choice == '5':
            card_id = int(input("Enter card ID for transaction: "))
            amount = float(input("Enter transaction amount: "))
            transaction_type = input("Enter transaction type (Credit/Debit): ")
            if transaction_type in ['Credit', 'Debit']:
                add_transaction(card_id, amount, transaction_type, user['user_id'])
            else:
                print("Invalid transaction type.")
        elif choice == '6':
            card_id = int(input("Enter card ID to view transactions: "))
            transactions = view_transactions(card_id)
            for transaction in transactions:
                print(transaction)
        elif choice == '7':
            break
        else:
            print("Invalid choice.")

def main():
    create_tables()
    while True:
        print("1. Login")
        print("2. Sign Up")
        choice = input("Enter your choice: ")

        if choice == '1':
            user = login()
            if user:
                if user['role'] == 'admin':
                    admin_menu(user)
                else:
                    user_menu(user)
        elif choice == '2':
            username = input("Enter a username: ")
            password = input("Enter a password: ")
            role = input("Enter role (admin/user): ")
            register_user(username, password, role)
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
