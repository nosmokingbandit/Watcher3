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
    .done(function(response){
        if(response){
            loc = window.location.href;
            if(loc.endsWith('/')){
                loc = loc.slice(0, -1);
            }
            if(loc.split("/").pop() == "auth"){
                window.location = url_base+"/library/status"
            } else {
                location.reload()
            }
        } else {
            $input_password.val("");
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })

}