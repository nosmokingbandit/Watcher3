$(document).ready(function () {
    $thinker = $("div#thinker");
    $thinker.show();

    $.post(url_base + "/ajax/server_status", {
        "mode": "shutdown"
    });

    /*
    This repeats every 3 seconds to check. Eventually I"ll put a counter in that shows an error message if it takes too long to restart.
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
            $thinker.css("opacity", 0);
            $("div.message").css("opacity", 0);
            $("div#content").css("background-position", "50% 45%");
        })
    }, 3000);
});
