import time
import os

import requests

import schedule

import psycopg2

import datetime

import pytz

tz = pytz.timezone("Asia/Tokyo")


def send_line_notify(notification_message):
    """
    LINEに通知する
    """
    line_notify_token = os.environ["NOTIFY_TOKEN"]
    line_notify_api = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {line_notify_token}"}
    data = {"message": f"message: {notification_message}"}
    requests.post(line_notify_api, headers=headers, data=data)


def task():
    message = ""

    with psycopg2.connect(os.environ["DATABASE_URL"]) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT name, event_date FROM event""")
            result = cursor.fetchall()

            for res in result:
                name: str = res[0]
                date: datetime.date = res[1]
                message += f"""\n{date}の{name}まであと{(date-datetime.datetime.now(tz).date()).days}日"""

        connection.commit()

    if message == "":
        message = "今後の予定はありません"

    send_line_notify(message)


schedule.every().day.at("09:00", tz).do(task)


def notify():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    notify()
