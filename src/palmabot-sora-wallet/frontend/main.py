class create_new_sora_wallet:
    def GET(self):
        # TODO: create sora wallet store to localstorage and store to db 
        data = web.input(chat_id='')
        
        if data:
            if data.get('chat_id'):
                # check if this chat_id already has sora wallet
                res = db.query("""SELECT * FROM sora_wallets WHERE chat_id=$chat_id""", vars={'chat_id': data.chat_id}).list()
                if res:
                    dd['msg'] = 'User already has active SORA wallet...'
                else:
                    # create here sora wallet and insert into db - only for PROTOTYPE !!! -> wallet will then be generated on client side !!!
                    from substrateinterface import Keypair, KeypairType

                    # Generate a new keypair
                    mnemonic = Keypair.generate_mnemonic()
                    keypair = Keypair.create_from_mnemonic(mnemonic, crypto_type=KeypairType.SR25519, ss58_format=69)
                    
                    dd = {'success': 1, 'msg': 'Create new SORA wallet.', 'ukaz': 'create_new_sora_wallet', 'wallet_public':  keypair.ss58_address, 'wallet_private': '', 'wallet_seed': mnemonic}
                    db.insert('sora_wallets', wallet_public=keypair.ss58_address, wallet_private='', wallet_seed=mnemonic, chat_id=data.chat_id, status=1)
        return render.create_new_sora_wallet(json.dumps(dd))

    def POST(self):
        # store wallet to db and localstorage and notify user via db and PUB
        data = web.input()
        dd = {}
        dd['msg'] = 'SORA wallet successfully created.'
        # now we have all - publish via PUB to palma thread listener
        db.insert('orders', data=json.dumps(dd) , status=1)
        return json.dumps(dd)


class sora_sign_transaction:
    def GET(self):
        # sign transaction and send to Palma wallet
        data = web.input(chat_id='', token_id='', amount='', to_address='cnSyrwqG6Wuwq3oxjiLUEWjSaJ1Bc4EJC2hKyKiFLJrxTxeiQ')
        dd = {
            'token_id': data.token_id,
            'amount': data.amount,
            'address_to': data.to_address,
        }
        return render.sora_sign_transaction(dd)

    def POST(self):
        # store wallet to db and localstorage and notify user via db and PUB
        data = web.input()
        dd = {}
        dd['msg'] = 'SORA wallet successfully created.'
        # now we have all - publish via PUB to palma thread listener
        db.insert('orders', data=json.dumps(dd) , status=1)
        return json.dumps(dd)
    