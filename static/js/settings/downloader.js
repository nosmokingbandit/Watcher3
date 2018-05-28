window.addEventListener("DOMContentLoaded", function(){
    $select_usenet = document.querySelector('select#usenet_client');
    $select_torrent = document.querySelector("select#torrent_client");

    $torrent_clients = document.querySelectorAll("div#torrent_client_settings > div");
    $usenet_clients = document.querySelectorAll("div#usenet_client_settings > div");

    // Set selects on page load
    each($usenet_clients, function(client){
        if(client.dataset.enabled == 'True'){
            client.style.maxHeight = '100%';
            $select_usenet.value = client.id;
            return false;
        }
    })

    each($torrent_clients, function(client){
        if(client.dataset.enabled == 'True'){
            client.style.maxHeight = '100%';
            $select_torrent.value = client.id;
            return false;
        }
    })

    $select_usenet.addEventListener('change', function(event){
        var val = event.target.value;
        each($usenet_clients, function(client){

            if(client.id == val){
                client.style.maxHeight = '100%';
            } else {
                client.style.maxHeight = '0%';
            }
        })
    });

    $select_torrent.addEventListener('change', function(event){
        var val = event.target.value;
        each($torrent_clients, function(client){
            client.style.maxHeight = '0%';
            if(client.id == val){
                client.style.maxHeight = '100%';
            }
        })
    });
});


function test_connection(event, button, mode){
    event.preventDefault();
    if(mode == 'usenet'){
        var client = $select_usenet.value;
    } else if(mode == 'torrent'){
        var client = $select_torrent.value;
    } else {
        return;
    }

    var $i = button.children[0];

    $i.classList.remove('mdi-lan-pending');
    $i.classList.add('mdi-circle');
    $i.classList.add('animated');

    var inputs = document.querySelectorAll("div#" + client + " input");

    var settings = {};
    each(inputs, function(input){
        settings[input.dataset.id] = parse_input(input);
    });

    settings = JSON.stringify(settings);

    $.post(url_base + "/ajax/test_downloader_connection", {
        "mode": client,
        "data": settings
    })
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]});
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $i.classList.remove('mdi-circle');
        $i.classList.add('mdi-lan-pending');
        $i.classList.remove('animated');
    });
}


function _get_settings(){

    var settings = {};
    settings["Sources"] = {};
    settings["Torrent"] = {};
    settings["Usenet"] = {};
    var blanks = false;

// DOWNLOADER['USENET']
    each(document.querySelectorAll("div#usenet_client_settings > div"), function(client){
        var name = client.id;
        var config = {};
        config['enabled'] = (client.style.maxHeight == '100%')

        each(client.querySelectorAll('i.c_box'), function(checkbox){
            config[checkbox.dataset.id] = is_checked(checkbox);
        });

        each(client.querySelectorAll('input, select'), function(input){
            config[input.dataset.id] = parse_input(input);
        });

        settings['Usenet'][name] = config;
    });

// DOWNLOADER['TORRENT']
    each(document.querySelectorAll("div#torrent_client_settings > div"), function(client){
        var name = client.id;
        var config = {};
        config['enabled'] = (client.style.maxHeight == '100%')

        each(client.querySelectorAll('i.c_box'), function(checkbox){
            config[checkbox.dataset.id] = is_checked(checkbox);
        });

        each(client.querySelectorAll('input, select'), function(input){
            config[input.dataset.id] = parse_input(input);
        });

        settings['Torrent'][name] = config;
    });

    settings['Torrent']['DelugeWeb']['category'] = settings['Torrent']['DelugeWeb']['category'].toLowerCase().replace(/[^a-z0-9_-]/g, '')
    settings['Torrent']['DelugeRPC']['category'] = settings['Torrent']['DelugeRPC']['category'].toLowerCase().replace(/[^a-z0-9_-]/g, '')

// DOWNLOADER['SOURCES']
    if($select_usenet.value){
        settings['Sources']['usenetenabled'] = true;
    } else {
        settings['Sources']['usenetenabled'] = false;
    }

    if($select_torrent.value){
        settings['Sources']['torrentenabled'] = true;
    } else {
        settings['Sources']['torrentenabled'] = false;
    }

    return {"Downloader": settings}
}


function register_putio(){
    var client_id = '3328';
    var redirect = encodeURIComponent('https://nosmokingbandit.github.io/putioregister');
    url = `https://api.put.io/v2/oauth2/authenticate?client_id=${client_id}&response_type=token&redirect_uri=${redirect}`;
    window.open(url, '_blank');
}
