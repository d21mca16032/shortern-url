import sqlite3

with sqlite3.connect('urls.db') as conn:
    cursor = conn.cursor()
    res = cursor.execute(
        'DELETE FROM WEB_URL'
    )

    conn.commit()
