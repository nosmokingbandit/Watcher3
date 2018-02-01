$(document).ready(function () {
    $input_api_key = document.querySelector('input#apikey');
});

function new_key(event){
    event.preventDefault();
    var key = _generate_key(32);
    $input_api_key.value = key;
};

function update_check(event, elem){
    event.preventDefault();
    $this = $(elem);

    var original_content = $this[0].innerHTML;

    $this.html("<i class='mdi mdi-circle animated'></i>");


    $.post(url_base + "/ajax/update_check", {})
    .done(function(response){
        show_notifications(response[1]);
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $this.html(original_content);
    });
}

function update_now(){
    $.post(url_base + "/ajax/update_server", {"mode": "set_true"})
    .done(function(){
        window.location = url_base + "/update";
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
};

function _get_settings(){

    var settings = {};
    settings["Proxy"] = {};
    var blanks = false;

// SERVER
    var required_fields = ['serverhost', 'serverport', 'keeplogs', 'apikey', 'checkupdatefrequency']

    each(document.querySelectorAll("form[data-category='server'] i.c_box"), function(checkbox){
        settings[checkbox.id] = is_checked(checkbox);
    })


    if(settings['customwebroot']){
        required_fields.push("customwebrootpath")
    }
    if(settings['authrequired']){
        required_fields.push("authuser", "authpass")
    }
    if($("input#ssl_cert").val() || $("input#ssl_key").val()){
        required_fields.push("ssl_cert", "ssl_key")
    }

    each(document.querySelectorAll("form[data-category='server'] input, form[data-category='server'] select"), function(input){
        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return
        }
        settings[input.id] = parse_input(input);
    })

// SERVER['PROXY']
    each(document.querySelectorAll("form[data-category='proxy'] i.c_box"), function(checkbox){
        settings['Proxy'][checkbox.id] = is_checked(checkbox);
    })

    if(settings['Proxy']['enabled']){
        required_fields = ["host", "port"];
    } else {
        required_fields = [];
    }

    each(document.querySelector("form[data-category='proxy']").querySelectorAll('input, select'), function(input){
        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return
        }

        settings['Proxy'][input.id] = parse_input(input);
    });

    if(blanks == true){
        return false;
    };

    return {"Server": settings}
}

function _generate_key(length){
    var text = "";
    var possible = "abcdef0123456789";
    for(var i = 0; i < length; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    };
    return text;
};
