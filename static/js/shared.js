$(document).ready(function() {
    url_base = $("meta[name='url_base']").attr("content");
    show_notifs = JSON.parse($("meta[name='enable_notifs']").attr("content") || "true");

    if(show_notifs){
        notifs = JSON.parse($("textarea#notifications_json").text());

        $.each(notifs, function(i, notif){
            notif[1]["onClose"] = remove_notif;
            var n = $.notify(notif[0], notif[1]);
            n["$ele"].attr("data-index", notif[1]["index"]);
        });
    }
});

$.notifyDefaults({type: "success",
                    allow_dismiss: true,
                    delay: 3000,
                    placement: {from: "bottom"},
                    animate: {enter: 'animated fadeInDown',
                            exit: 'animated fadeOutDown'
                            }
                    });

function remove_notif(){
    var index = $(this).data("index");
    if(index === undefined){
        return false;
    }
    $.post(window.url_base + "/ajax/notification_remove", {
        "index": index
    })
}


function format_template(t, d){
    for(var p in d){
        t=t.replace(new RegExp('{'+p+'}','g'), d[p]);
    }
    return t;
}


function _start_update(event){
    // Method called to start update from notification.
    event.preventDefault();
    $.post(url_base + "/ajax/update_now", {"mode": "set_true"})
    .done(function(){
        window.location = url_base + "/system/update";
    });
}
