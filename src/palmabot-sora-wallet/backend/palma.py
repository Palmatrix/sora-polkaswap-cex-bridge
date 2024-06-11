@run_async
@check_user
def delete_sora_wallet(bot, update):
    """prototype delete SORA wallet"""
    mydb = db.Db()
    my.p('[User {} entered delete_sora_wallet command.'.format(update.message.chat_id))

    my_text = '<b>Delete SORA wallet</b>'
    bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 

    # check if this user already has SORA wallet
    sql = """DELETE FROM sora_wallets WHERE chat_id=%s RETURNING *"""
    sora_wallet = mydb.execute_one(sql, (str(update.message.chat_id),))
    if sora_wallet:
        my_text = f"""<b>Your SORA wallet {sora_wallet['wallet_public']} deleted!</b>"""
        bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 
    else:
        my_text = 'No active SORA wallet.'
        button_list = [
                        telegram.InlineKeyboardButton( t.t("Create new SORA wallet", update.message.chat_id), url='{}/createnewsorawallet?chat_id={}'.format( g.SERVER_NAME, update.message.chat_id))
                        ]

        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=1))
        bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML, reply_markup=reply_markup) 

@run_async
@check_user
def create_sora_wallet(bot, update):
    """prototype create SORA wallet"""
    mydb = db.Db()

    my.p('[User {} entered create_sora_wallet command.'.format(update.message.chat_id))

    my_text = '<b>Create new SORA wallet</b>'
    bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 

    # check if this user already has SORA wallet
    sql = """SELECT * FROM sora_wallets WHERE chat_id=%s AND status=1"""
    sora_wallet = mydb.execute_one(sql, (str(update.message.chat_id),))
    if sora_wallet:
        my_text = '<b>You already have SORA wallet!</b>'
        bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 
        
        my_text = '<b>{}</b>'.format(sora_wallet['wallet_public'])
        bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 
        
        # show QR code
        button_list = [
            telegram.InlineKeyboardButton('Balance', callback_data='get_sora_user_balance|{}'.format(update.message.chat_id)),
            telegram.InlineKeyboardButton('Transactions', callback_data='get_sora_user_transactions|{}'.format(update.message.chat_id)),
            telegram.InlineKeyboardButton('Send XOR', callback_data='send_xor|{}'.format(update.message.chat_id))
        ]
        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))
        img = mytools.generate_qr(sora_wallet['wallet_public'])
        if img:
            updater.bot.send_photo(chat_id=update.message.chat_id, photo=open(img, 'rb'), timeout=100, reply_markup=reply_markup)
            # delete image
            os.remove(img)
    else:
        my_text = 'Creating new SORA wallet will create\n\n(1) public wallet address,\n(2) your private key and\n(3) SEED set of words.\n\n Please store them in safe place.'
        button_list = [
                        telegram.InlineKeyboardButton( t.t("Create new SORA wallet", update.message.chat_id), url='{}/createnewsorawallet?chat_id={}'.format( g.SERVER_NAME, update.message.chat_id))
                        ]

        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=1))
        bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML, reply_markup=reply_markup) 


@run_async
@check_user
def show_sora_wallet(bot, update):
    """prototype show QR code for SORA wallet"""
    mydb = db.Db()

    my.p('[User {} entered sora_wallet command.'.format(update.message.chat_id))
    my_text = '<b>SORA wallet</b>\n\nPublic address and QR code for SORA wallet (XOR).'
    # show text
    bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 
    # get SORA wallet for this user
    sql = """SELECT * FROM sora_wallets WHERE chat_id=%s AND status=1"""
    sora_wallet = mydb.execute_one(sql, (str(update.message.chat_id),))
    if sora_wallet:
        my_text = '<b>{}</b>'.format(sora_wallet['wallet_public'])
        bot.send_message(update.message.chat_id, disable_web_page_preview=False, text=my_text, parse_mode=telegram.ParseMode.HTML) 
        
        # show QR code
        # TODO: create buttons to show balance, transactions, send
        button_list = [
            telegram.InlineKeyboardButton('Balance', callback_data='get_sora_user_balance|{}'.format(update.message.chat_id)),
            telegram.InlineKeyboardButton('Transactions', callback_data='get_sora_user_transactions|{}'.format(update.message.chat_id)),
            telegram.InlineKeyboardButton('Send XOR', callback_data='send_xor|{}'.format(update.message.chat_id))
        ]
        reply_markup = telegram.InlineKeyboardMarkup(mytools.build_menu(button_list, n_cols=3))
        img = mytools.generate_qr(f"""substrate:{sora_wallet['wallet_public']}:{sora_wallet['wallet_public_hex']}:PalmaTest:0x0200000000000000000000000000000000000000000000000000000000000000""")
        if img:
            updater.bot.send_photo(chat_id=update.message.chat_id, photo=open(img, 'rb'), timeout=100, reply_markup=reply_markup)
            # delete image
            os.remove(img)
    else:
        # TODO: create buttons to add wallet
        bot.send_message(update.message.chat_id, text='SORA wallet not found for this user.\n\n/createSoraWallet', reply_markup=gumbi.default_markup(update.message.chat_id), parse_mode=telegram.ParseMode.HTML)
    
    
