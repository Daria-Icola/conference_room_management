import psycopg2
import datetime
import os

def connect_data(db_user, db_password, host, port, db):
 return psycopg2.connect(user=db_user, password=db_password, host=host, port=port, database=db)


def update_end_time(db_user, db_password, host, port, db):
    conn = connect_data(db_user, db_password, host, port, db)
    cur = conn.cursor()
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    insert_into_booking = f'''UPDATE users_booking
    SET end_datetime = end_datetime - INTERVAL '1 MINUTE'
    WHERE start_datetime >= %s;
        '''
    cur.execute(insert_into_booking, (current_date,))
    conn.commit()
    print("Обновлено")
    cur.close()
    conn.close()


update_end_time(db_user=os.getenv("DB_USER"), db_password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"))

