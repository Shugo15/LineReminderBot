FROM python:3.11

WORKDIR /bot
COPY requirements.txt /bot/

RUN pip install --upgrade -r requirements.txt

COPY . /bot

CMD python -u main.py