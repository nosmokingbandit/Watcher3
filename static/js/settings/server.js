$(document).ready(function () {
    $input_api_key = $("input#apikey");
    git_url = $("span#git_url").text();
});

function new_key(event){
    event.preventDefault();
    var key = _generate_key(32);
    $input_api_key.val(key);
};

function update_check(event, elem){
    event.preventDefault();
    $this = $(elem);

    var original_content = $this[0].innerHTML;

    $this.html("<i class='mdi mdi-circle-outline animated'></i>");


    $.post(url_base + "/ajax/update_check", {})
    .done(function(response){
        if(response["status"] == "current"){
            $.notify({message: 'No Updates Available.'}, {type: 'primary'})
        } else if(response["status"] == "error"){
            $.notify({message: response["error"]}, {type: "danger"});
        } else if(response["status"] == "behind"){

            if(response["behind_count"] == 1){
                title = response["behind_count"] + " Update Available:<br/>";
            } else {
                title = response["behind_count"] + " Updates Available:<br/>";
            };

            compare = git_url + "/compare/" + response["local_hash"] + "..." + response["new_hash"]

            body = "Click <a onclick='_start_update(event)'><u>here</u></a> to update now. <br/> Click <a href=" + compare + " target=_blank><u>here</u></a> to view changes."

            $.notify({title: title, message: body}, {delay: 0})
        }
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

    $("form[data-category='server'] i").each(function(){
        var $this = $(this);
        settings[$this.attr("id")] = is_checked($this);
    });

    if(settings['customwebroot']){
        required_fields.push("customwebrootpath")
    }
    if(settings['authrequired']){
        required_fields.push("authuser", "authpass")
    }

    $("form[data-category='server'] :input:not(button)").each(function(){
        var $this = $(this);

        if($this.val() == "" && required_fields.includes($this.attr("id"))){
            $this.addClass("empty");
            blanks = true;
            return;
        }

        if($this.attr("type") == "number"){
            var min = parseInt($this.attr("min"));
            var val = Math.max(parseInt($this.val()), min);
            settings[$this.attr("id")] = val || min;
        }
        else{
            settings[$this.attr("id")] = $this.val();
        }
    });

// SERVER['PROXY']
    $("form[data-category='proxy'] i").each(function(){
        $this = $(this);
        settings["Proxy"][$this.attr("id")] = is_checked($this);
    });


    if(settings['Proxy']['enabled']){
        required_fields = ["host", "port"];
    } else {
        required_fields = [];
    }

    $("form[data-category='proxy'] :input:not(button)").each(function(){
        $this = $(this);

        if($this.val() == "" && required_fields.includes($this.attr("id"))){
            $this.addClass("empty");
            blanks = true;
            return;
        }

        if($this.attr("type") == "number"){
            var min = parseInt($this.attr("min"));
            var val = Math.max(parseInt($this.val()), min);
            settings["Proxy"][$this.attr("id")] = val || min;
        }
        else{
            settings['Proxy'][$this.attr("id")] = $this.val();
        }
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
