$(document).ready(function(){
    var updating = $("meta[name='updating']").attr("content");

    if(updating.toLowerCase() == 'false'){
        window.location = url_base + "/library/status/";
        return;
    }

    $thinker = $("div#thinker");
    $thinker.show();

    $message = $("div.message");

    document.title = "Watcher - Updating Server";
    var last_response_len = false;
    $.ajax(url_base + '/ajax/update_server', {
        method: "POST",
        data: {"mode": "update_now"},
        xhrFields: {
            onprogress: function(e){
                var response_update;
                var response = e.currentTarget.response;
                if(last_response_len === false){
                    response_update = response;
                    last_response_len = response.length;
                } else {
                    response_update = response.substring(last_response_len);
                    last_response_len = response.length;
                }
                var r = JSON.parse(response_update);

                var $tasks_list = $("div.tasks")

                if(r["response"] == false){
                    $thinker.fadeOut();
                    $.notify({message: r["error"]}, {type: "danger", delay: 0});
                    return
                }
                else if(r["status"] == "waiting"){
                    $tasks_list.show();
                    $thinker.css("opacity", "0.25")
                    var $active_tasks = $("div.tasks > div")
                    var active_names = [];

                    $active_tasks.each(function(index, element){
                        var $task = $(element);
                        var name = $task.text();
                        active_names.push(name);
                        if(r["active_tasks"].indexOf(name) == -1){
                            $task.slideUp();
                        }
                    });

                    $(r["active_tasks"]).each(function(index, name){
                        if(active_names.indexOf(name) == -1){
                            $tasks_list.append(`<div>${name}</div>`)
                        }
                    });
                }
                else if(r["status"] == "updating"){
                    $tasks_list.fadeOut();
                    $thinker.css("opacity", 1);
                    $("div.updating").fadeIn();
                }
                else if(r["status"] == "complete"){
                    $.notify({message: _("Update successful.")}, {delay: 0});
                    $("div.updating").text(_("Restarting."));
                    restart();
                }
            }
        }
    })
    .done(function(data){
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    });
});


function restart(){
    /*
    This repeats every 3 seconds to check. Times out after 10 attempts and
        shows span.error message.
    */
    document.title = "Watcher - Restarting Server";
    var try_count = 0
    var check = setInterval(function(){
        if(try_count < 10){
            try_count += 1;
            $.post(url_base + "/ajax/server_status", {
                mode: "online",
            })
            .done(function(r){
                if(r != "states.STOPPING"){
                    window.location = url_base+"/library/status/";
                }
            });
        } else {
            clearInterval(check);
            $.notify({title: "<u>Timout Exceeded</u><br/>", message: "Watcher is taking too long to restart. Please check your logs and restart manually."}, {type: "warning", delay: 0})
            $thinker.css("opacity", 0);
        }
    }, 3000);
}
