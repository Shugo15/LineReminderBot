import os

from flask import Flask, request, abort

from waitress import serve

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

import psycopg2


app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("""[text] {event.message.text}""")

    Commands.help(event)

    Commands.register(event)

    Commands.delete(event)

    Commands.show(event)

    Commands.melton(event)


prefix = "!"


class Commands:
    def help(event):
        tokens = event.message.text.split()

        if len(tokens) != 1:
            return

        if tokens[0] != f"{prefix}help":
            return

        reply_message = (
            f"{prefix}register name date : イベントを登録\n"
            f"※dateはYYYY-MM-DDの形式\n"
            f"\n"
            f"{prefix}delete name date : イベントを削除\n"
            f"\n"
            f"{prefix}show : 全てのイベントを表示"
        )

        print("ヘルプを表示")

        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_message))

    def register(event):
        tokens = event.message.text.split()

        if len(tokens) != 3:
            return

        if tokens[0] != f"{prefix}register":
            return

        with psycopg2.connect(os.environ["DATABASE_URL"]) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT MAX(id) AS max_id FROM event""")
                result = cursor.fetchone()

                if result[0] == None:
                    id = 0
                else:
                    id = result[0] + 1

                cursor.execute(
                    """INSERT INTO event (id, name, event_date) VALUES (%s,%s, %s)""",
                    [id, tokens[1], tokens[2]],
                )

            connection.commit()

        print("イベントを登録")

        line_bot_api.reply_message(event.reply_token, TextSendMessage("イベントを登録しました"))

    def delete(event):
        tokens = event.message.text.split()

        if len(tokens) != 3:
            return

        if tokens[0] != f"{prefix}delete":
            return

        with psycopg2.connect(os.environ["DATABASE_URL"]) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT COUNT(*) FROM event""")
                result = cursor.fetchone()
                before_columns = result[0]

                cursor.execute(
                    """DELETE FROM event WHERE name = %s AND event_date = %s""",
                    [tokens[1], tokens[2]],
                )

                cursor.execute("""SELECT COUNT(*) FROM event""")
                result = cursor.fetchone()
                after_columns = result[0]

                delete_count = before_columns - after_columns

            connection.commit()

        print(f"{delete_count}件のイベントを削除")

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(f"{delete_count}件のイベントを削除しました")
        )

    def show(event):
        tokens = event.message.text.split()

        if len(tokens) != 1:
            return

        if tokens[0] != f"{prefix}show":
            return

        with psycopg2.connect(os.environ["DATABASE_URL"]) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""SELECT name, event_date FROM event""")
                result = cursor.fetchall()

            connection.commit()

        print("イベントを表示")

        if len(result) == 0:
            reply_message = "イベントはありません"
        else:
            reply_message = "[イベント一覧]\n"

        for index, res in enumerate(result):
            reply_message += f"イベント名 : {res[0]}\n日付 : {res[1]}"

            if index != len(result) - 1:
                reply_message += "\n\n"

        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_message))

    def melton(event):
        tokens = event.message.text.split()

        if len(tokens) != 1:
            return

        if tokens[0] != f"{prefix}melton":
            return

        line_bot_api.reply_message(event.reply_token, TextSendMessage("ﾄﾞｩﾒﾙﾄﾝﾃﾞｰｽ!"))


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=os.environ["PORT"])
