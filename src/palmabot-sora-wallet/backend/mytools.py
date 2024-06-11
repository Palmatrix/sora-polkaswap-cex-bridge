def send_xor(bot, update, user_data):
    try:
        user_chat_id = update.callback_query.message.chat.id
    except Exception as e:
        user_chat_id = update.message.chat_id
        
    mystr = 'You will send 10 XOR from your SORA wallet to PALMA wallet.'
    button_list = [
                telegram.InlineKeyboardButton( t.t("Sign and send transaction", user_chat_id), url='{}/sorasigntransaction?chat_id={}&token_id=0x02&amount=10'.format( g.SERVER_NAME, user_chat_id))
                ]
    reply_markup = telegram.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    bot.send_message(chat_id=user_chat_id, text=mystr, parse_mode=telegram.ParseMode.HTML, reply_markup=reply_markup)        


    return 1

def get_sora_user_balance(bot, update, user_data):
    try:
        user_chat_id = update.callback_query.message.chat.id
    except Exception as e:
        user_chat_id = update.message.chat_id
        
    mystr = 'Getting balance(s) from SORA network. Please wait...'
    bot.send_message(chat_id=user_chat_id, text=mystr, parse_mode=telegram.ParseMode.HTML, reply_markup=gumbi.default_markup(user_chat_id))        

    from substrateinterface import SubstrateInterface, Keypair
    from substrateinterface.utils.ss58 import ss58_decode

    # Connect to the SORA network
    substrate = SubstrateInterface(url="wss://sora.api.onfinality.io/public-ws", 
                                   type_registry_preset='substrate-node-template',
                                   ss58_format=69)
    # Get the chain id
    chain_id = substrate.chain
    print(f"Chain ID: {chain_id}")
    
    # Assume mydb is an instance of your database handler
    mydb = db.Db()

    # Fetch the public key from the database
    public_key = mydb.execute_one("""SELECT * FROM sora_wallets WHERE chat_id = %s""", (str(user_chat_id),))
    print(public_key)

    # Query the balance
    balance_info = substrate.query(
        module='System',
        storage_function='Account',
        params=[public_key['wallet_public']]
    )

    mystr = """<b>Your SORA wallet balance(s):</b>\n\n"""

    if balance_info:
        # check if user has sora account
        mystr += f"""Balance(s): {balance_info['data']['free']}"""
        print(f"{balance_info['data']['free']}")
    else:
        mystr += f"""Balance not available."""
        print("Failed to fetch balance.")

    bot.send_message(chat_id=user_chat_id, text=mystr, parse_mode=telegram.ParseMode.HTML, reply_markup=gumbi.default_markup(user_chat_id))        

    return 1
