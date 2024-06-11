$( document ).ready(function() {

    data = $('#data_dict').val()
    d = JSON.parse(data)

    // CREATE SORA WALLET in JS and store values to localstorage
    if (d) {
        localStorage.setItem('sora_wallet_public', d['wallet_public']);
        localStorage.setItem('sora_wallet_private', d['wallet_private']);
        localStorage.setItem('sora_wallet_seed', d['wallet_seed']);
        $('#mydiv').html("SORA wallet created successfully.<br>SORA WALLET ADDRESS: " + d['wallet_public'] + "<br>PRIVATE KEY: "+ d['wallet_private'] + "<br>SEED: "+ d['wallet_seed'])
    } else{
        $('#mydiv').html("SORA wallet already created.");
    }
   


});
