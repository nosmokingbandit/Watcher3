window.addEventListener("DOMContentLoaded", function(){
    mapping_template = document.querySelector("template#template_mapping").innerHTML;
    $mapping_table = document.querySelector('form[data-category="remote_mapping"] tbody');
});

function add_mapping(event, elem){
    event.preventDefault();
    $mapping_table.insertAdjacentHTML('beforeend', mapping_template);
}

function remove_mapping(event, elem){
    event.preventDefault();
    var $tr = $(elem).closest('tr');
    $tr.fadeOut(500, function(){
                        $tr.remove();
                     });
}

function _get_settings(){
    var settings = {};
    settings["RemoteMapping"] = {};
    settings["Scanner"] = {};
    var blanks = false;

// POSTPROCESSING
    var required_fields = [];

    each(document.querySelectorAll("form[data-category='postprocessing'] i.c_box"), function(checkbox){
        settings[checkbox.id] = is_checked(checkbox);
    })

    if(settings['renamerenabled']){
        required_fields.push('renamerstring')
    }

    if(settings['moverenabled']){
        required_fields.push('moverpath')
    }

    if(settings['recyclebinenabled']){
        required_fields.push('recyclebindirectory')
    }

    each(document.querySelectorAll("form[data-category='postprocessing'] input, form[data-category='postprocessing'] select"), function(input){
        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return;
        }
        settings[input.id] = input.value;
    });

// POSTPROCESSING["SCANNER"]
    each(document.querySelectorAll("form[data-category='scanner'] i.c_box"), function(checkbox){
        settings['Scanner'][checkbox.id] = is_checked(checkbox);
    });

    if(settings["Scanner"]["enabled"] == true){
        required_fields.push("directory", "interval");
    }


    each(document.querySelectorAll("form[data-category='scanner'] input, form[data-category='scanner'] select"), function(input){

        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return;
        }
        settings['Scanner'][input.id] = parse_input(input);

    });

    // POSTPROCESSING["REMOTEMAPPING"]
    each(document.querySelectorAll("form[data-category='remote_mapping'] tbody > tr"), function(row){
        var $remote = row.querySelector('input[data-id="remote"]');
        var remote = $remote.value;
        var $local = row.querySelector('input[data-id="local"]');
        var local = $local.value;

        if(!remote && !local){
            return;
        } else if(remote && !local){
            $local.classList.add('border-danger');
            blanks = true;
        } else {
            settings['RemoteMapping'][remote] = local;
        }

    });

    if(blanks == true){
        return false;
    };

    return {'Postprocessing': settings}
}
