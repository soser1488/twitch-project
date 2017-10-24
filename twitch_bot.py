from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import requests
import settings
from bs4 import BeautifulSoup
import json
import work
from models import Subscription, db_session, Streamers
from sqlalchemy.orm import Query



logging.basicConfig(format='%(name)s - %(asctime)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='bot.log'
                    )
def start_bot(bot, update):
    user_chat = update.message.chat
    chat_id = user_chat.id
    first_name = user_chat.first_name
    last_name = user_chat.last_name
    username = user_chat.username

    add_user = work.user_db_add_user(chat_id, first_name, last_name, username)
    logging.info('Попытка добавления пользователя {}: {}'.format(chat_id, add_user))
    update.message.reply_text('Привет')
    logging.info('Пользователь {} {} ({} {}) нажал /start'.format(chat_id, first_name, last_name, username))   
    

#users = set()
def subscription(bot, update):
    chat_id = update.message.chat.id
    print("adding new channel_id {}".format(chat_id))
    #users.add(chat_id)
    streamer_name = update.message.text[5:]
    logging.info(streamer_name)
    print(chat_id, streamer_name)
    streamer_id = work.db_add_streamer(streamer_name)
    add_subs = work.subscriptions_db_add_sub(chat_id, streamer_id)
    text = 'Вы успешно подписались на стримера {}'.format(streamer_name)
    update.message.reply_text(text)






def callback_minute(bot, job):
    for streamer in Streamers.query.all():
        print('ssss')
        print(streamer)
        twitch_request = requests.get('https://api.twitch.tv/kraken/streams/{}?on_site=1&client_id=5y09vdm04uriqa6zfi7hjdb68z7b3r'.format(streamer.streamer_name))
        json_data = twitch_request.json()
        stream_value = json_data['stream']
        print(stream_value)
        print(type(stream_value))
        if stream_value is  None:
            streamer.stream_type = None
            db_session.commit()
            print("NONE")
        elif stream_value['stream_type'] == 'live':
            print('LIVE')
            if streamer.stream_type is None:
                streamer.stream_type = 'live'
                db_session.commit()
                for streamer1 in Subscription.query.filter(Subscription.id == streamer.id):
                    bot.send_message(chat_id = streamer1.user_id,
                                    text = """{0} только что начал стрим, быстрей туда
https://twitch.tv/{0}""".format(stream_value['channel']['display_name']))


def unsubscription(bot, update):
    chat_id = update.message.chat.id
    streamer_name = update.message.text[7:]
    streamer_id = Streamers.query.filter(Streamers.streamer_name == streamer_name).first()
    streamer_id = streamer_id.id
    logging.info("{} try unsub from {}".format(chat_id, streamer_name))
    user_to_unsub = Subscription.query.filter(Subscription.user_id == chat_id, Subscription.streamer_id == streamer_id).first()
    print(user_to_unsub)

    print('unsub sucsess')
    try:
        db_session.delete(user_to_unsub)
        db_session.commit()
        update.message.reply_text("Вы успешно отписались от {}".format(streamer_name))
    except sqlalchemy.orm.exc.UnmappedInstanceError:
        update.message.reply_text("Вы не подписаны на такого стримера")
        db_session.rollback()


def main():
    upd = Updater(settings.TELEGRAM_API_KEY)
    job = upd.job_queue
    job_minute = job.run_repeating(callback_minute, interval = 60, first = 0)
    logging.info('callback worked')
    upd.dispatcher.add_handler(CommandHandler("unsub", unsubscription))
    upd.dispatcher.add_handler(CommandHandler("sub", subscription))
    upd.dispatcher.add_handler(CommandHandler("start", start_bot))
    upd.start_polling()
    upd.idle()



if __name__ == "__main__":
    logging.info('bot started')
    main()