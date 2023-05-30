import psycopg2
import os


def connect_data(db_user, db_password, host, port, db):
    return psycopg2.connect(user=db_user, password=db_password, host=host, port=port, database=db)


def delete_previous_booking(db_user, db_password, host, port, db):
    conn = connect_data(db_user, db_password, host, port, db)
    cur = conn.cursor()
    request_to_db = f'''DELETE FROM users_booking
    WHERE end_datetime::date < CURRENT_TIMESTAMP::date;'''
    cur.execute(request_to_db)
    conn.commit()
    print("Старые записи удалены")
    cur.close()
    conn.close()


delete_previous_booking(db_user=os.getenv("DB_USER"), db_password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), db=os.getenv("DB_NAME"))

