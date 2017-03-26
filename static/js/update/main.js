$(document).ready(function () {
    var url_base = $("meta[name='url_base']").attr("content");
    var updating = $("meta[name='updating']").attr("content");

    if(updating == 'false'){
        window.location = url_base + "/status/";
        return;
    }

    $("div#thinker").show();

    /*
    This repeats every 3 seconds to check if the server is back online.
    Sends the browser to /restart if it is started.
    This sometimes creates an error in CherryPy because we ask for a response
        when the server is turned off, but this is ok.
    */

    $.post(url_base + "/ajax/update_now", {
        "mode": "update_now"
    })
    .done(function(r){
        response = JSON.parse(r);
        if(response["response"] == false){
            $("#thinker").fadeOut();
            $("span.msg").text("Update failed. Check logs for more information.");

        }else if(response["response"] == true){
            // if the update succeeds we"ll start checking for the server to come back online
            var check = setInterval(function(){
                $.post(url_base + "/ajax/server_status", {
                    "mode": "online"
                })
                .done(function(r){
                    if(r == "states.STARTED"){
                        $("span.msg").text("Update successful!");
                        setTimeout(function() {window.location =  url_base + "/restart/";},3000);
                    }
                })
                .fail(function(r){
                    return;
                });
            }, 3000);

        }else{
            $("#thinker").fadeOut();
            $("span.msg").text("Unknown response. Check logs for more information.");
        }
    });
});
