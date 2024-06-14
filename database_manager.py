import sqlite3

class DatabaseManager:
    def __init__(self, db_name='weather_bot.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
                        user_id INTEGER PRIMARY KEY, 
                        location TEXT, 
                        send_time TEXT)''')
        conn.commit()
        conn.close()

    def save_location(self, user_id, location):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO subscriptions (user_id, location) VALUES (?, ?)', (user_id, location))
        conn.commit()
        conn.close()

    def update_send_time(self, user_id, send_time):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('UPDATE subscriptions SET send_time = ? WHERE user_id = ?', (send_time, user_id))
        conn.commit()
        conn.close()

    def get_subscription(self, user_id):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT location, send_time FROM subscriptions WHERE user_id = ?', (user_id,))
        result = c.fetchone()
        conn.close()
        return result

    def get_all_subscriptions(self):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute('SELECT user_id, location, send_time FROM subscriptions')
        results = c.fetchall()
        conn.close()
        return results
