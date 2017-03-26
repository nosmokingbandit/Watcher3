$(document).ready(function(){
    var url_base = $("meta[name='url_base']").attr("content");
    window.url_base = url_base;
    var enabled = $("meta[name='enable_notifs']").attr("content");
    if(enabled == 'false'){
        return false;
    }

    var notifs = JSON.parse($("meta[name='notifications']").attr("content"));

    $.each(notifs, function(index, notif){
        type = notif['type'];
        body = notif['body'];
        title = notif['title'];
        params = notif['params'];

        if(params['onclick'] != undefined){
            params['onclick'] = window[params['onclick']]
        }

        params['onCloseClick'] = remove_notif;
        params['index'] = index;

        toastr[type](body, title, params);

    });


    $(document).on('click', 'div#toast-container a', function(e){
        e.preventDefault();
        $this = $(this);

        url = $this.attr('href');

        if($this.attr('href') == 'update_now'){
            update_now();
            return false
        } else{
            window.open(url, '_blank');
            return false
        }

    });


});

/* starts update process and redirects browser */
function update_now(){
    $.post(url_base + "/ajax/update_now", {"mode": "set_true"})
    .done(function(){
        window.location = url_base + "/update";
    });
};

/* sends post to remove notification from list */
function remove_notif(){
    index = this['index']
    $.post(window.url_base + "/ajax/notification_remove", {
        "index": index
    })
}
