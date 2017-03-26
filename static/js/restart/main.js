$(document).ready(function () {

    $("div#thinker").show();

    var url_base = $("meta[name='url_base']").attr("content");

    $.post(url_base + "/ajax/server_status", {
        mode: 'restart'
    });

    /*
    This repeats every 3 seconds to check. Times out after 10 attempts and
        shows span.error message.
    */
    var try_count = 0
    var check = setInterval(function(){
        if(try_count < 10){
            $.post(url_base + "/ajax/server_status", {
                mode: "online",
            })
            .done(function(r){
                if(r != "states.STOPPING"){
                    window.location = url_base + '/';
                }
            });
        }
        else {
            clearInterval(check);
            $('span.msg').text('');
            $('span.error').show();
            $('#thinker').hide();
        }
    }, 3000);
});
