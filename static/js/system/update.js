$(document).ready(function () {
    var updating = $("meta[name='updating']").attr("content");

    if(updating.toLowerCase() == 'false'){
        window.location = url_base + "/library/status/";
        return;
    }

    $thinker = $("div#thinker");
    $thinker.show();

    $message = $("div.message");

    /*
    This repeats every 3 seconds to check if the server is back online.
    Sends the browser to /restart if it is started.
    This sometimes creates an error in CherryPy because we ask for a response
        when the server is turned off, but this is ok.
    */

    $.post(url_base + "/ajax/update_now", {
        "mode": "update_now"
    })
    .done(function(response){
        if(response["response"] == false){
            $thinker.css("opacity", 0);
            $message.css("opacity", 0);

            $.notify({title: "<u>Update Failed</u><br/>", message: "Please check logs for more information."}, {type: "danger", delay: 0})

        }else if(response["response"] == true){
            // if the update succeeds we"ll start checking for the server to come back online
            var check = setInterval(function(){
                $.post(url_base + "/ajax/server_status", {
                    "mode": "online"
                })
                .done(function(r){
                    if(r == "states.STARTED"){
                        $.notify({message: "Update successful."}, {delay: 0});
                        setTimeout(function() {window.location =  url_base + "/system/restart/";}, 2500);
                    }
                })
                .fail(function(r){
                    return;
                });
            }, 3000);

        } else {
            $thinker.css("opacity", 0);
            $message.css("opacity", 0);
            $.notify({title: "<u>Update Failed</u><br/>", message: "Please check logs for more information."}, {type: "danger", delay: 0})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
});
