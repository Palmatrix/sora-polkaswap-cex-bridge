
import os
import mytools, db, g, grafi, gumbi
from myutils import printing

import datetime, time

import telegram
from telegram import (ReplyKeyboardMarkup)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, RegexHandler

import translate as t

# initiate printing and file logging management
my = printing(os.path.realpath(__file__),'log/palma.log')

def relocate(img):
    path_img = '/var/www/palmabot/graph/{}'.format(img)
    os.rename(img,path_img)
    return 1

def relocated_path(img):
    return '/var/www/palmabot/graph/{}'.format(img)


# TODO: join this with same myutils function
def check_user(my_func):
    # print(my_func.__name__)
    def wrapper(*args, **kwarg):
        mydb = db.Db()
        s = time.time()
        # TODO: put all users into memory (when new user is added, deleted or modified also add to memory)

        sql = """SELECT * FROM users WHERE chat_id=%s AND status = 1"""

        if args[1].message:
            user_chat_id = str(args[1].message.chat_id)
        else:
            user_chat_id = str(args[1].callback_query.message.chat.id)
            args[1].callback_query.answer()

        try:
            res = mydb.execute_one(sql, (user_chat_id, ))
        except Exception as e:
            print('Something went wrong in wrapper function: {}'.format(e))
            return my_func(*args, **kwarg)

        if res:
            if not res['rate_limit_ts']:
                print('First time setting rate_limit_ts...')
                mydb.execute_one("""UPDATE users SET rate_limit_ts=%s WHERE id=%s RETURNING id""", (datetime.datetime.now(), res['id']))
            elif res['rate_limit_ts'] > datetime.datetime.now()-datetime.timedelta(seconds=2):
                print('User {} is rate limiting... presing callback buttons too fast. {}s between clicks. - dropping this out...'.format(user_chat_id, datetime.datetime.now()-res['rate_limit_ts']))
                return None
            else:
                mydb.execute_one("""UPDATE users SET rate_limit_ts=%s WHERE id=%s RETURNING id""", (datetime.datetime.now(), res['id']))

        else:
            # this is only when user was in palmabot but was erased from database
            # this is for testing only - after deletion of
            if int(user_chat_id) < 0:
                my.d("""You are in a group. Chat with me directly here <a href="https://t.me/palma11bot">PalmaBot</a>""", 'telegram', user_chat_id)
            else:
                args[0].send_message(user_chat_id, text='Try /start or contact our support admin@palmabot.com to activate your account.')
            return None
        # print('wrapper: {}s'.format(time.time()-s))
        return my_func(*args, **kwarg)

    return wrapper


@check_user
def signal_callback(bot, update, user_data):
    user_chat_id = update.callback_query.message.chat.id
    mydbi = db.Db_insert()
    mydb = db.Db()
    mydbi.log_to_db(update.callback_query.message.chat.id, 'signal_callback', update.callback_query.data)
    my_list = update.callback_query.data.split("|")
    my.p('Callback function user {} clicked {}'.format(update.callback_query.message.chat.id, update.callback_query.data))
    my.d('Callback function. User: {}, User_data: {}, callback_text: {} callback_data: {}'.format(update.callback_query.message.chat, user_data, [update.callback_query.message.text],
                                                                                             update.callback_query.data))
    if my_list[0] == 'send_xor':
        my.d('send xor')
        mytools.send_xor(bot, update, user_data)
        update.callback_query.answer()

    elif my_list[0] == 'get_sora_user_balance':
        my.d('get_sora_user_balance')
        mydbi.log_to_db(user_chat_id, 'call_back', 'get_sora_user_balance')
        mytools.get_sora_user_balance(bot, update, user_data)
        update.callback_query.answer()
        
    elif my_list[0] == 'user_coin':
        bot.send_message(chat_id=user_chat_id, text=t.t('Getting data...', user_chat_id), reply_markup=gumbi.default_markup(user_chat_id))
        my.d('user_coin')
        mydbi.log_to_db(user_chat_id, 'call_back', 'user_coin')
        mystr = 'price {} {} {}'.format(my_list[1], my_list[2], my_list[3])
        mytools.getPrice(bot, update, user_data, mystr)
        update.callback_query.answer()

    elif my_list[0] == 'mute':
        buttons = []
        setting = my_list[1]
        value = my_list[2]
        if value == '1':
            value = 0
        else:
            value = 1

        # update only this json field in database users table
        user = mydb.execute_one("""update users set settings=jsonb_set(settings, '{{{}}}', '{}'::jsonb) where chat_id='{}' RETURNING *""".format(setting, value, str(user_chat_id)))
        # TODO toggle button and edit chat message
        if user:
            if user['settings']: # settings in form: {'news':1, 'marketing':1, 'social':1}
                
                for key, value in user['settings'].items():
                    buttons.append(telegram.InlineKeyboardButton('ON ' + t.t(key, user_chat_id) if value else 'OFF ' + t.t(key, user_chat_id), callback_data='mute|{}|{}'.format(key, value)))
        bot.editMessageText(text=t.t('<b>Toggle chat-bot communication ON/OFF</b>\n\n<b>news:</b>\nImportant crypto news delivery.\n\n<b>social:</b>\nHow other users are doing?\n\n<b>marketing:</b>\nPalmaBot tips, new features, token promotions etc.', str(user_chat_id)), chat_id=user_chat_id, message_id=update.callback_query.message.message_id, reply_markup=telegram.InlineKeyboardMarkup(mytools.build_menu(buttons, n_cols=3)), parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=False)
        update.callback_query.answer()

    elif my_list[0] == 'deactivate_xc_command':
        mydbi.execute("""UPDATE xc_automate SET status=0 WHERE command_id=%s AND chat_id=%s""", (my_list[1], str(user_chat_id)))
        mytext = t.t("""<b>Strategy automation #{} successfully deactivated.</b>""", user_chat_id).format(my_list[1])
        bot.send_message(user_chat_id, text=mytext, parse_mode=telegram.ParseMode.HTML)
        update.callback_query.answer()

    elif my_list[0] == 'next_order':
        mytext = """<b>Set up next order:</b>\n\nPlease choose which order would you like to be executed after previous one is finished:"""
        button_list = [
            telegram.InlineKeyboardButton(t.t("buy", user_chat_id),  callback_data="buy"),
            telegram.InlineKeyboardButton(t.t("trailing stop sell", user_chat_id), callback_data='trailing_stop_sell'),
            telegram.InlineKeyboardButton(t.t("sell", user_chat_id), callback_data="sell"),
            telegram.InlineKeyboardButton(t.t("stop loss take profit", user_chat_id), callback_data="sl_tp"),
            telegram.InlineKeyboardButton(t.t("repeat order", user_chat_id), callback_data="repeat_order")
        ]
        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=2))
        bot.send_message(user_chat_id, text=mytext + '\n\n<b>This command not supported jet.</b> If you would like to have this command supported, please vote in our <a href="https://t.me/PalmaBotCommunity">PalmaBot community channel</a>.', reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
        update.callback_query.answer()
    elif my_list[0] == 'pro_active':
        sql = """SELECT * FROM users WHERE chat_id=%s"""
        ures = mydb.execute_one(sql, (str(user_chat_id),))
        if ures ['demo'] == 1:
            # user in DEMO mode
            sql = """SELECT order_id, order_status, order_name, action, amount, coin_name, market_name, exchange_name, price, status, status_name, created_ts, status_ts FROM palma_trading_orders 
                WHERE chat_id=%s AND status != 4 AND order_status = 1 AND demo = 1 
                GROUP BY order_id, order_status, order_name, action, amount, coin_name, 
                market_name, exchange_name, price, status, status_name, created_ts, status_ts ORDER BY order_id ASC"""
            res = mydb.execute_all(sql, (str(user_chat_id),))
        else:
            sql = """SELECT order_id, order_status, order_name, action, amount, coin_name, market_name, exchange_name, price, status, status_name, created_ts, status_ts FROM palma_trading_orders 
            WHERE chat_id=%s AND status != 4 AND order_status = 1 AND (demo IS NULL OR demo = 0)
            GROUP BY order_id, order_status, order_name, action, amount, coin_name, 
            market_name, exchange_name, price, status, status_name, created_ts, status_ts ORDER BY order_id ASC"""
            res = mydb.execute_all(sql, (str(user_chat_id),))

        order_id = -1
        order_status = 0

        for r in res:
            order_status = r['order_status']
            if order_id == -1:
                order_id = r['order_id']  # show only first time
                mytext = t.t('<b>{} order #{} created {}</b>\n\n', user_chat_id).format(r['exchange_name'].capitalize(), order_id,
                                                                     r['created_ts'].strftime('%d.%m.%Y %H:%M'))

            if r['order_id'] == order_id:
                button_list = [
                    telegram.InlineKeyboardButton(t.t("deactivate", user_chat_id),
                                                  callback_data='deactivate_palma_order|{}'.format(order_id)),
                    telegram.InlineKeyboardButton(t.t("price", user_chat_id),
                                                  callback_data="price|{}|{}|{}".format(r['coin_name'],
                                                                                        r['market_name'],
                                                                                        r['exchange_name'])),
                    telegram.InlineKeyboardButton(t.t("edit", user_chat_id),
                                                  callback_data="edit_order|{}|{}".format(order_id, r['market_name']))
                ]
                reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))

                if r['status_ts']:
                    status_timestamp = r['status_ts'].strftime('%d.%m.%Y %H:%M')
                else:
                    status_timestamp = ''

                if not (r['order_name'] == 'SL_TP' and r['action'] == 'BUY'):
                    mytext = mytext + t.t('{} {} {} at price {} {} [{} {}]\n', user_chat_id).format(r['action'], mytools.d(r['amount']),
                                                                             r['coin_name'].upper(),
                                                                             mytools.d(r['price']), r['market_name'],
                                                                             r['status_name'], status_timestamp)
            else:
                if r['order_status']:
                    bot.send_message(user_chat_id, text=mytext, parse_mode=telegram.ParseMode.HTML,
                                     reply_markup=reply_markup)
                else:
                    bot.send_message(user_chat_id, text=mytext, parse_mode=telegram.ParseMode.HTML)

                if r['status_ts']:
                    status_timestamp = r['status_ts'].strftime('%d.%m.%Y %H:%M')
                else:
                    status_timestamp = ''

                order_id = r['order_id']
                mytext = t.t('<b>{} order #{} created {}</b>\n\n', user_chat_id).format(r['exchange_name'].capitalize(), order_id,
                                                                     r['created_ts'].strftime('%d.%m.%Y %H:%M'))
                if not (r['order_name'] == 'SL_TP' and r['action'] == 'BUY'):
                    mytext = mytext + t.t('{} {} {} at price {} {} [{} {}]\n', user_chat_id).format(r['action'], mytools.d(r['amount']), r['coin_name'].upper(), mytools.d(r['price']), r['market_name'], r['status_name'],status_timestamp)

                button_list = [
                    telegram.InlineKeyboardButton(t.t("deactivate", user_chat_id),
                                                  callback_data='deactivate_palma_order|{}'.format(order_id)),
                    telegram.InlineKeyboardButton(t.t("price", user_chat_id),
                                                  callback_data="price|{}|{}|{}".format(r['coin_name'],
                                                                                        r['market_name'],
                                                                                        r['exchange_name'])),
                    telegram.InlineKeyboardButton(t.t("edit", user_chat_id),
                                                  callback_data="edit_order|{}|{}".format(order_id, r['market_name']))
                ]
                reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))

        if order_id == -1:  # there are no active orders at the moment
            mytext = t.t("""<b>No active orders.</b>\n\nCreate new order with /palmaPRO.""", user_chat_id)
            bot.send_message(user_chat_id, text=mytext, parse_mode=telegram.ParseMode.HTML)
        else:
            if order_status:
                button_list = [
                    telegram.InlineKeyboardButton(t.t("deactivate", user_chat_id),
                                                  callback_data='deactivate_palma_order|{}'.format(order_id)),
                    telegram.InlineKeyboardButton(t.t("price", user_chat_id),
                                                  callback_data="price|{}|{}|{}".format(r['coin_name'],
                                                                                        r['market_name'],
                                                                                        r['exchange_name'])),
                    telegram.InlineKeyboardButton(t.t("edit", user_chat_id),
                                                  callback_data="edit_order|{}|{}".format(order_id, r['market_name']))
                ]
                reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))
                bot.send_message(user_chat_id, text=mytext, parse_mode=telegram.ParseMode.HTML,
                                 reply_markup=reply_markup)
            else:
                bot.send_message(user_chat_id, text=mytext, parse_mode=telegram.ParseMode.HTML)

        update.callback_query.answer()
    elif my_list[0] == 'deactivate_diff':
        for m in mytools.deactivateDiffSignal(update.callback_query.data, update.callback_query.message.chat.id):
            bot.send_message(update.callback_query.message.chat.id, text='{}'.format(m), parse_mode=telegram.ParseMode.HTML)
        update.callback_query.answer()
    elif my_list[0] == 'deactivate_abs':
            for m in mytools.deactivate_abs_signal(update.callback_query.data, update.callback_query.message.chat.id):
                bot.send_message(update.callback_query.message.chat.id, text='{}'.format(m),
                                 parse_mode=telegram.ParseMode.HTML)
            update.callback_query.answer()
    elif my_list[0] == 'deactivate_palma_order':
        # cancel palma trading order
        sql = """UPDATE palma_trading_orders SET status=4, order_status=0, status_name='deactivated', status_ts = %s WHERE order_id = %s"""
        mydbi.execute(sql, (datetime.datetime.now(), my_list[1], ))
        mytext = t.t("""Palma trading order #{} successfully deactivated!""", user_chat_id).format(my_list[1])
        bot.send_message(update.callback_query.message.chat.id, text=mytext, parse_mode=telegram.ParseMode.HTML, reply_markup=gumbi.pro(user_chat_id))
        update.callback_query.answer()
    elif my_list[0] == 'receive_coins':
        #  generate QR my coin address
        mydb = db.Db()
        coin_name = my_list[1]
        sql = """SELECT * FROM coins WHERE abbr = %s AND status=1"""
        res = mydb.execute_one(sql, (coin_name,))
        coin_id = res['coin_id']
        exchange_id = my_list[2]
        user_chat_id = update.callback_query.message.chat.id
        sql = """SELECT * FROM users WHERE chat_id=%s"""
        ures = mydb.execute_one(sql, (str(user_chat_id),))
        if ures:
            sql = """SELECT * FROM user_exchange_coin_wallet WHERE user_id=%s AND exchange_id=%s AND coin_id=%s AND status=1"""
            res = mydb.execute_one(sql, (ures['id'], exchange_id, coin_id))

        # generate QR
        if res:
            if res['wallet_address']:
                bot.send_message(update.callback_query.message.chat.id, text=t.t('Your wallet address and QR code:\n{}', user_chat_id).format(res['wallet_address']), parse_mode=telegram.ParseMode.HTML)
                img = ''
                img = mytools.generate_qr('{}'.format(res['wallet_address']))
                if img:
                    bot.send_photo(chat_id=user_chat_id, photo=open(img, 'rb'), timeout=100)
            else:
                bot.send_message(update.callback_query.message.chat.id, text=t.t('No wallet address for this coin. Generating new...', user_chat_id), parse_mode=telegram.ParseMode.HTML)
                wa = mytools.get_andor_generate_wallet_address(ures['id'], 0, coin_id)
                bot.send_message(update.callback_query.message.chat.id, text=t.t('New wallet address for {}:\n{}', user_chat_id).format(coin_name, wa), parse_mode=telegram.ParseMode.HTML)
                img = ''
                img = mytools.generate_qr('{}'.format(wa))
                if img:
                    bot.send_photo(chat_id=user_chat_id, photo=open(img, 'rb'), timeout=100)

        else:
            bot.send_message(update.callback_query.message.chat.id, text=t.t('No wallet address for this coin. Generating new...', user_chat_id), parse_mode=telegram.ParseMode.HTML)
            wa = mytools.get_andor_generate_wallet_address(ures['id'], 0, coin_id)
            bot.send_message(update.callback_query.message.chat.id, text=t.t('New wallet address for {}:\n{}', user_chat_id).format(coin_name, wa), parse_mode=telegram.ParseMode.HTML)
            img = ''
            img = mytools.generate_qr('{}'.format(wa))
            if img:
                bot.send_photo(chat_id=user_chat_id, photo=open(img, 'rb'), timeout=100)

        update.callback_query.answer()


    elif my_list[0] == 'pro_order_view':
        # show order details
        sql = """SELECT * FROM palma_trading_orders WHERE order_id=%s ORDER BY id"""
        res = mydb.execute_all(sql, (my_list[1], ))
        first = 1
        if res:

            for r in res:
                if first:
                    mytext = '<b>{} order #{} created {}</b>\n\n'.format(r['exchange_name'].capitalize(), my_list[1], r['created_ts'].strftime('%d.%m.%Y %H:%M'))
                    first = 0

                if r['status_ts']:
                    status_timestamp = r['status_ts'].strftime('%d.%m.%Y %H:%M')
                else:
                    status_timestamp = ''
                if r['action'] == 'SELL_SL' and r['is_trailing']:
                    mytext = mytext + t.t('{} {} {} at price {} {} - trailing [{} {}]\n', r['chat_id']).format(r['action'], mytools.d(r['amount']), r['coin_name'].upper(),
                                                                                 mytools.d(r['price']), r['market_name'], r['status_name'], status_timestamp)

                else:
                    mytext = mytext + t.t('{} {} {} at price {} {} [{} {}]\n', r['chat_id']).format(r['action'], mytools.d(r['amount']), r['coin_name'].upper(),
                                                                             mytools.d(r['price']), r['market_name'], r['status_name'], status_timestamp)
            if res[0]['order_status'] == 1:
                if len(res) == 1:
                    button_list = [
                        telegram.InlineKeyboardButton(t.t("deactivate", r['chat_id']),
                                                      callback_data='deactivate_palma_order|{}'.format(r['order_id'])),
                        telegram.InlineKeyboardButton(t.t("price", r['chat_id']),
                                                      callback_data="price|{}|{}|{}".format(r['coin_name'], r['market_name'],
                                                                                            r['exchange_name']))

                    ]
                    reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))
                else:
                    button_list = [
                        telegram.InlineKeyboardButton(t.t("deactivate", r['chat_id']),
                                                      callback_data='deactivate_palma_order|{}'.format(r['order_id'])),
                        telegram.InlineKeyboardButton(t.t("price", r['chat_id']),
                                                      callback_data="price|{}|{}|{}".format(r['coin_name'], r['market_name'],
                                                                                            r['exchange_name'])),
                        telegram.InlineKeyboardButton(t.t("edit", r['chat_id']), callback_data="edit_order|{}|{}".format(r['order_id'], r['market_name']))

                    ]
                    reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))
                bot.send_message(update.callback_query.message.chat.id, text=mytext, reply_markup=reply_markup, parse_mode=telegram.ParseMode.HTML)
            else:
                bot.send_message(update.callback_query.message.chat.id, text=mytext, parse_mode=telegram.ParseMode.HTML, reply_markup=gumbi.pro_order_finish(dict(res[0])))
        update.callback_query.answer()

    elif my_list[0] == 'cancel_open_order':
        mytools.cancelOpenOrder(update.callback_query.message.chat.id,my_list[1],my_list[2])
        update.callback_query.answer()
    
    elif my_list[0] == 'ena':
        mystr = t.t('<b>2|4 real-time signals</b>\n\nBitcoin price changed for 5%!\n\nSet your own signals with /signal and avoid FOMO.\n\n', update.callback_query.message.chat.id)
        button_list = [telegram.InlineKeyboardButton(t.t("next tip", update.callback_query.message.chat.id), callback_data='dva|dva')]
        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=1))
        bot.editMessageText(text=mystr, chat_id=update.callback_query.message.chat.id, message_id=update.callback_query.message.message_id, reply_markup=reply_markup,
                            parse_mode=telegram.ParseMode.HTML)
        mydbi.log_to_db(update.callback_query.message.chat.id, 'walk through', '1|4')
        update.callback_query.answer()
    elif my_list[0] == 'dva':
        mystr = t.t('<b>3|4 /demo</b>\n\nFirst timer?\n\nNo problem, turn on demo and trade risk free.', update.callback_query.message.chat.id)
        button_list = [ telegram.InlineKeyboardButton(t.t("next tip", update.callback_query.message.chat.id), callback_data='tri|tri') ]
        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=1))
        bot.editMessageText(text=mystr, chat_id=update.callback_query.message.chat.id, message_id=update.callback_query.message.message_id, reply_markup=reply_markup,
                            parse_mode=telegram.ParseMode.HTML)
        mydbi.log_to_db(update.callback_query.message.chat.id, 'walk through', '2|4')
        update.callback_query.answer()
    elif my_list[0] == 'tri':
        mystr = t.t('<b>4|4 /PalmaPRO</b>\n\nWant to become a PRO?\n\nThere is much more than just simple /buy /sell /transfer and /balance It is up to you when you are ready.\n\n<a href="{}/settings?chat_id={}">Connect your favourite exchange</a> and start trading on the go.\n\nPalmaBot the fastest multi-exchange trading bot.', update.callback_query.message.chat.id).format(g.SERVER_NAME, user_chat_id)
        button_list = [ telegram.InlineKeyboardButton(t.t("finish", update.callback_query.message.chat.id), callback_data='stiri|stiri') ]
        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=1))
        bot.editMessageText(text=mystr, chat_id=update.callback_query.message.chat.id, message_id=update.callback_query.message.message_id, reply_markup=reply_markup,
                            parse_mode=telegram.ParseMode.HTML)
        mydbi.log_to_db(update.callback_query.message.chat.id, 'walk through', '3|4')
        update.callback_query.answer()
    elif my_list[0] == 'stiri':

        sql = """SELECT * FROM user_exchange_coin_price_diff_hunter WHERE chat_id='{}'""".format(update.callback_query.message.chat.id)
        res = mydb.execute_one(sql)
        if res:
            mystr = t.t('Great. I can see that you already have /diff signal activated :)\n\nWherever you are, use /coinPrice to check your favorite coin price.', update.callback_query.message.chat.id)
            create_signal = 0
        else:
            mystr = t.t('/Signals\n\nAvoid FOMO with our price alert signals !\n\nI have created btc@eur diff signal on Bitstamp for you. I will notify you when price changes for 3%. ', update.callback_query.message.chat.id)

            create_signal = 1
        bot.editMessageText(text=mystr, chat_id=update.callback_query.message.chat.id, message_id=update.callback_query.message.message_id, parse_mode=telegram.ParseMode.HTML)
        mydbi.log_to_db(update.callback_query.message.chat.id,'walk through','4|4')

        if create_signal:
            # create one default signal for user
            ask = 0
            bid = 0
            try:
                ask = mydb.get_ask('bitstamp', 'btc', 'eur')
                bid = mydb.get_bid('bitstamp', 'btc', 'eur')
            except Exception as e:
                my.p('Can not get price from matrica to create /start signal:{}'.format(e), 'W')
            if ask and bid:
                try:
                    mydbi.execute("""INSERT INTO user_exchange_coin_price_diff_hunter (chat_id,exchange_id,exchange_name,coin_id,coin_abbr,market_id,market_abbr,last_price,last_price_ts,price,
                    price_ts,treshold,ask,bid,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""", (update.callback_query.message.chat.id, 22, 'bitstamp', 1, 'btc', 12,
                                                                                                                              'EUR', (ask+bid)/2, datetime.datetime.now(), (ask+bid)/2,
                                                                                                                              datetime.datetime.now(), 3, ask, bid, 1))
                except Exception as e:
                    my.p(e, 'W')
        update.callback_query.answer()
    elif my_list[0] == 'list_signals':
        my.d('callback_list_signals')
        mydbi.log_to_db(user_chat_id, 'call_back', 'list_signals')
        for m in mytools.manageSignals(user_chat_id):
            if 'You don\'t have any active signals.' in m[2]:
                bot.send_message(user_chat_id, text=t.t('{}\nUse /Signal to create new signals.', user_chat_id).format(m[2]), parse_mode=telegram.ParseMode.HTML)
            else:
                bot.send_message(user_chat_id, text='{}'.format(m[2]), parse_mode=telegram.ParseMode.HTML, reply_markup=gumbi.signal_list(m[0], m[1], m[4], m[5], m[3], user_chat_id))
        update.callback_query.answer()
    elif my_list[0] == 'price':
        my.d('callback_price')
        mydbi.log_to_db(user_chat_id, 'call_back', 'price')
        mystr = '{} {} {} {}'.format(my_list[0], my_list[1], my_list[2], my_list[3])
        mytools.getPrice(bot, update, user_data, mystr)
        update.callback_query.answer()
    elif my_list[0] == 'news':
        my.d('callback_news')
        mydbi.log_to_db(user_chat_id, 'call_back', 'news')
        for m in mytools.getnews('{} {}'.format(my_list[0], my_list[1])):
            bot.send_message(user_chat_id, text="{}".format(m), parse_mode=telegram.ParseMode.HTML)
        bot.send_message(user_chat_id, text=t.t("Create new /diff signal, /buy or /sell coins.", user_chat_id))
        update.callback_query.answer()
    elif my_list[0] == 'arbi_show_coins':
        my.d('callback_arbi_show_coins z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id, 'call_back', 'arbi_show_coins')

        button_list = []
        sql = """SELECT * FROM neo WHERE updated_ts > '{}' AND profit between 0 and 0.15""".format((datetime.datetime.now()-datetime.timedelta(hours=12)))
        neo_res = mydb.execute_all(sql)
        for r in neo_res:
            if r['coin_name'] not in button_list:
                button_list.append("{}".format(r['coin_name']))

        reply_keyboard = mytools.build_menu(sorted(button_list), n_cols=5)

        bot.send_message(user_chat_id, text=t.t("Please select coin:", user_chat_id), parse_mode=telegram.ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
        update.callback_query.answer()
    elif my_list[0] == 'arbi_show_markets':
        my.d('callback_arbi_show_markets z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id,'call_back','arbi_show_markets')
        button_list = []

        # Show arbi for choosen market
        sql = """SELECT * FROM neo WHERE updated_ts > '{}' AND profit between 0 and 0.15""".format( (datetime.datetime.now()-datetime.timedelta(hours=12)))
        neo_res = mydb.execute_all(sql)
        for r in neo_res:
            if r['market_name'] not in button_list:
                button_list.append("{}".format(r['market_name']))

        reply_keyboard = mytools.build_menu(sorted(button_list), n_cols=5)
        bot.send_message(user_chat_id, text=t.t("Please select market:", user_chat_id), parse_mode=telegram.ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
        update.callback_query.answer()
    elif my_list[0] == 'arbi_show_exchanges':
        my.d('callback_arbi_show_exchanges z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id,'call_back','arbi_show_exchanges')

        button_list = []
        sql = """SELECT * FROM neo WHERE updated_ts > '{}' AND profit between 0 and 0.15""".format( (datetime.datetime.now()-datetime.timedelta(hours=12)))
        neo_res = mydb.execute_all(sql)
        for r in neo_res:
            if r['exchange1_name'] not in button_list:
                button_list.append("{}".format(r['exchange1_name']))
        reply_keyboard = mytools.build_menu(sorted(button_list), n_cols=5)
        bot.send_message(user_chat_id, text=t.t("Please select exchange:", user_chat_id), parse_mode=telegram.ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True))
        update.callback_query.answer()

    elif my_list[0] == '1h':
        my.d('callback_1h z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id, 'call_back', '1h')

        # create graph
        try:
            params = {}
            params['coin_abbr'] = my_list[1]
            params['market_abbr'] = my_list[2]
            params['exchange_name'] = my_list[3]
            params['msg_id'] = update.callback_query.message.message_id
            params['interval'] = 1
            mygr = grafi.Graf()
            image_name = mygr.graf(params, True, user_chat_id)  # second parameter is for generating image file
            if image_name:
                relocate(image_name)  # move to http
                success = 1
            else:
                success = 0
        except Exception as e:
            success = 0
            my.d('Error creating graph: {}'.format(e),'W')

        reply_markup = gumbi.graf(params['coin_abbr'], params['market_abbr'], params['exchange_name'])

        if success:
            try:
                bot.edit_message_media(chat_id=user_chat_id, message_id=params['msg_id'], 
                media=telegram.InputMediaPhoto('{}/graph/{}'.format(g.SERVER_NAME, image_name)),
                                       reply_markup=reply_markup)
            except Exception as e:
                my.d(str(e), 'W')
            os.remove(relocated_path(image_name))
        update.callback_query.answer()

    elif my_list[0] == '4h':
        my.d('callback_4h z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id, 'call_back', '4h')
        # naredi graf za 6h in pošlji slikico z call back gumbi

        # create graph
        try:
            params = {}
            params['coin_abbr'] = my_list[1]
            params['market_abbr'] = my_list[2]
            params['exchange_name'] = my_list[3]
            params['msg_id'] =  update.callback_query.message.message_id
            params['interval'] = 4
            mygr = grafi.Graf()
            image_name = mygr.graf(params, True, user_chat_id)
            if image_name:
                relocate(image_name)  # move to http
                success = 1
            else:
                success = 0

        except Exception as e:
            success = 0
            my.d('Error creating graph: {}'.format(e), 'W')

        reply_markup = gumbi.graf(params['coin_abbr'], params['market_abbr'], params['exchange_name'])

        if success:
            try:
                bot.edit_message_media(chat_id=user_chat_id, message_id=params['msg_id'], 
                media=telegram.InputMediaPhoto('{}/graph/{}'.format(g.SERVER_NAME, image_name)),
                                       reply_markup=reply_markup)
                update.callback_query.answer()
            except Exception as e:
                my.d(str(e),'W')
            os.remove(relocated_path(image_name))
        update.callback_query.answer()
    elif my_list[0] == '24h':
        my.d('callback_24h z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id, 'call_back', '24h')

        # create graph
        try:
            params = {}
            params['coin_abbr'] = my_list[1]
            params['market_abbr'] = my_list[2]
            params['exchange_name'] = my_list[3]
            params['msg_id'] = update.callback_query.message.message_id
            params['interval'] = 24
            mygr = grafi.Graf()
            image_name = mygr.graf(params, True, user_chat_id)
            if image_name:
                relocate(image_name)  # move to http
                success = 1
            else:
                success = 0

        except Exception as e:
            success = 0
            my.d('Error creating graph: {}'.format(e), 'W')

        reply_markup = gumbi.graf(params['coin_abbr'], params['market_abbr'], params['exchange_name'])

        if success:
            try:
                bot.edit_message_media(chat_id=user_chat_id, message_id=params['msg_id'], 
                media=telegram.InputMediaPhoto('{}/graph/{}'.format(g.SERVER_NAME, image_name)),
                                       reply_markup=reply_markup)
                update.callback_query.answer()
            except Exception as e:
                my.d(str(e),'W')
            os.remove(relocated_path(image_name))
        update.callback_query.answer()
    elif my_list[0] == '168h':

        # update.callback_query.answer(text='Loading...', show_alert=True, cache_time=3)
        
        my.d('callback_1w z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id, 'call_back', '1w')

        # create graph
        try:
            params = {}
            params['coin_abbr'] = my_list[1]
            params['market_abbr'] = my_list[2]
            params['exchange_name'] = my_list[3]
            params['msg_id'] = update.callback_query.message.message_id
            params['interval'] = 168
            mygr = grafi.Graf()
            image_name = mygr.graf(params, True, user_chat_id)
            if image_name:
                relocate(image_name)  # move to http
                success = 1
            else:
                success = 0

        except Exception as e:
            success = 0
            my.d('Error creating graph: {}'.format(e), 'W')

        reply_markup = gumbi.graf(params['coin_abbr'], params['market_abbr'], params['exchange_name'])

        if success:
            try:
                bot.edit_message_media(chat_id=user_chat_id, message_id=params['msg_id'],
                media=telegram.InputMediaPhoto('{}/graph/{}'.format(g.SERVER_NAME, image_name)),
                                       reply_markup=reply_markup)
                update.callback_query.answer()
            except Exception as e:
                my.d(str(e),'W')
            os.remove(relocated_path(image_name))
        update.callback_query.answer()
    elif my_list[0] == '720h':
        my.d('callback_1w z parametri:{}'.format(my_list))
        mydbi.log_to_db(user_chat_id, 'call_back', '1M')

        # create graph
        try:
            params = {}
            params['coin_abbr'] = my_list[1]
            params['market_abbr'] = my_list[2]
            params['exchange_name'] = my_list[3]
            params['msg_id'] = update.callback_query.message.message_id
            params['interval'] = 720
            mygr = grafi.Graf()
            image_name = mygr.graf(params, True, user_chat_id)
            if image_name:
                relocate(image_name)  # move to http
                success = 1
            else:
                success = 0

        except Exception as e:
            success = 0
            my.d('Error creating graph: {}'.format(e), 'W')

        reply_markup = gumbi.graf(params['coin_abbr'], params['market_abbr'], params['exchange_name'])

        if success:
            try:
                bot.edit_message_media(chat_id=user_chat_id, message_id=params['msg_id'],
                media=telegram.InputMediaPhoto('{}/graph/{}'.format(g.SERVER_NAME, image_name)),
                                       reply_markup=reply_markup)
                update.callback_query.answer()
            except Exception as e:
                my.d(str(e), 'W')
            os.remove(relocated_path(image_name))
        update.callback_query.answer()

    # elif my_list[0] == 'candle':
    #     my.d('callback_candle z parametri:{}'.format(my_list))
    #     mydbi.log_to_db(user_chat_id,'call_back','candle')
    #     # naredi graf za 6h in pošlji slikico z call back gumbi

    #     # create graph
    #     try:
    #         params = {}
    #         params['coin_abbr'] = my_list[1]
    #         params['market_abbr'] = my_list[2]
    #         params['exchange_name'] = my_list[3]
    #         params['msg_id'] = update.callback_query.message.message_id
    #         params['interval'] = 6
    #         mygr = grafi.Graf()
    #         image_name = mygr.candle(params)
    #         relocate(image_name) #move to http
    #         success = 1
    #     except Exception as e:
    #         success = 0
    #         my.d('Error creating graph: {}'.format(e),'W')

    #     reply_markup = gumbi.graf(params['coin_abbr'],params['market_abbr'],params['exchange_name'])

    #     if success:
    #         try:
    #             bot.edit_message_media(chat_id=user_chat_id, message_id=params['msg_id'], 
    #             media=telegram.InputMediaPhoto('{}/static/{}'.format(g.SERVER_NAME, image_name)),
    #                                    reply_markup=reply_markup)
    #             update.callback_query.answer()
    #         except Exception as e:
    #             my.d(str(e), 'W')
    #         os.remove(relocated_path(image_name))
    #     update.callback_query.answer()

    return ConversationHandler.END


