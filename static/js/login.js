$(document).ready(function(){
    url_base = $("meta[name='url_base']").attr("content");

    $("input").keyup(function(event){
        if(event.keyCode == 13){
            login(event);
        }
    });

    $("input").click(function(){
        $(this).removeClass("empty");
    });
});


function login(event){
    event.preventDefault();

    var $input_user = $('input#user');
    var user = $input_user.val();
    var $input_password = $('input#password');
    var password = $input_password.val();
    var blanks = false;

    if(!user){
        blanks = true;
        $input_user.addClass("empty");
    }

    if(!password){
        blanks = true;
        $input_password.addClass("empty");
    }

    if(blanks == true){
        return false;
    };

    $.post(url_base + "/auth/login", {
        "username": user,
        "password": password
    })
    .done(function(r) {
        if(JSON.parse(r)){
            location.reload()
        } else {
            $input_password.val("");
        }

    });

}