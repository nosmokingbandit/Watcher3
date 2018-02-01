$(document).ready(function () {
    document.title = "Watcher - Shutting Down Server";

    $thinker = document.getElementById("thinker");
    $thinker.style.maxHeight = '100%';

    $.post(url_base + "/ajax/server_status", {
        "mode": "shutdown"
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });

    /*
    This repeats every 3 seconds to check if the server is still online.
    */
    var try_count = 0
    var check = setInterval(function(){
        $.post(url_base + "/ajax/server_status", {
            "mode": "online",
        })
        .done(function(r){
            //do nothing
        })
        .fail(function(r){
            clearInterval(check);
            document.title = "Watcher";
            $thinker.style.maxHeight = '0%';
            $("div.message").css("opacity", 0);
            $("div#content").css("background-position", "50% 45%");
        })
    }, 3000);
});
