$(document).ready(function () {
    var url_base = $("meta[name='url_base']").attr("content");

    $("input").keyup(function(event){
        if(event.keyCode == 13){
            $("i#send_login").click();
        }
    });



    $('i#send_login').click(function(){
        var $input_username = $('input#username');
        var $input_password = $('input#password');
        var blanks = false;

        $("div#login_form input").each(function(){

            if($(this).val() == ''){
                blanks = true;
                highlight($(this));
            }
        });

        if(blanks == true){
            return false;
        };

        $.post(url_base + "/auth/login/", {
            "username": $input_username.val(),
            "password": $input_password.val()
        })

        .done(function(r) {
            location.reload();
        });

    });


    function highlight(element){
        orig_bg = element.css('background-color');
        element.css('background-color', '#f4693b');
        element.delay(500).animate({'background-color': orig_bg}, 1000);
    };

});
