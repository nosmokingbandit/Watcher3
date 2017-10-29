$(document).ready(function(){
    url_base = $("meta[name='url_base']").attr("content");
    show_notifs = JSON.parse($("meta[name='enable_notifs']").attr("content") || "true");
    language = $("meta[name='language']").attr("content") || "en";

    if(show_notifs){
        notifs = JSON.parse($("textarea#notifications_json").text());

        show_notifications(notifs);
    }
});

function show_notifications(notifs){
    /* Shows notifications in DOM
    notifs (list): tuples of notification options, settings
    */
    $.each(notifs, function(i, notif){
        notif[1]["onClose"] = remove_notif;
        var n = $.notify(notif[0], notif[1]);
        n["$ele"].attr("data-index", notif[1]["index"]);
    });
}

function logout(event){
    event.preventDefault();

    $.post(url_base+"/auth/logout", {})
    .done(function(r){
        window.location = r;
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
}

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
    });
}


function format_template(t, d){
    for(var p in d){
        t=t.replace(new RegExp('{'+p+'}','g'), d[p]);
    }
    return t;
}

function each(arr, fn){
    // Executes fn(array_item, array_index) for each item in arr
    var i = arr.length;
    while (--i >= 0){
        fn(arr[i], i)
    }
}

function _start_update(event){
    // Method called to start update from notification.
    event.preventDefault();
    $.post(url_base + "/ajax/update_server", {"mode": "set_true"})
    .done(function(){
        window.location = url_base + "/system/update";
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
}

function _(s){
    /* Localization method
    s (str): string to look for in translation file

    returns string
    */
    if(language == "en"){
        return s
    } else {
        return languages[language][s] || s;
    }


}