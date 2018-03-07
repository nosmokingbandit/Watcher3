window.addEventListener("DOMContentLoaded", function(){
    url_base = document.querySelector("meta[name='url_base']").content;

    $input_user = document.querySelector('input#user');
    $input_password = document.querySelector('input#password');

    $input_user.focus();

    var ins = document.querySelectorAll('input');
    for (var i = 0; i < ins.length; i++){
        var input = ins[i];
        input.addEventListener('keyup', function(event){
            if(event.keyCode == 13){
                login(event);
            }
        });
        input.addEventListener('click', function(event){
            input.classList.remove('border-danger');
        });
    }
});

function login(event){
    event.preventDefault();

    var blanks = false;

    if(!$input_user.value){
        blanks = true;
        $input_user.classList.add("border-danger");
    }

    if(!$input_password.value){
        blanks = true;
        $input_password.classList.add("border-danger");
    }

    if(blanks == true){
        return false;
    };

    $.post(url_base + "/auth/login", {
        "username": $input_user.value,
        "password": $input_password.value
    })
    .done(function(response){
        if(response){
            loc = window.location.href;
            if(loc.endsWith('/')){
                loc = loc.slice(0, -1);
            }
            if(loc.split("/").pop() == "auth"){
                window.location = url_base + "/library/status"
            } else {
                location.reload()
            }
        } else {
            $input_password.value = '';
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })

}
