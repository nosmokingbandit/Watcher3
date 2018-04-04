window.addEventListener("DOMContentLoaded", function(){
    template_config = document.querySelector("template#template_config").innerHTML;

});

function edit_plugin_conf(event, elem, folder, filename){
    event.preventDefault()
    var config_file;

    $.post(url_base + "/ajax/get_plugin_conf", {"folder": folder, "conf": filename})
    .done(function(config_html){
        if(!config_html){
            $.notify({message: _("Unable to read plugin config.")}, {type: "danger"})
            return false
        }

        var template_dictionary = {"name": filename.replace(".conf", ""),
                                   "folder": folder,
                                   "filename": filename,
                                   "config": config_html
                                   }

        $conf_modal = $(format_template(template_config, template_dictionary));

        $conf_modal.find("i.c_box").each(function(){
            if (this.getAttribute("value") == "True" ){
                this.classList.remove("mdi-checkbox-blank-outline")
                this.classList.add("mdi-checkbox-marked");
            }
        });

        $conf_modal.modal('show');

    })
    .fail(function(response){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });

    return
}

function save_plugin_conf(event, button){
    event.preventDefault()
    var config = {"Config Version": 2};

    $modal = $conf_modal[0];

    var icon = button.firstElementChild;

    icon.classList.remove('mdi-content-save');
    icon.classList.add('mdi-circle');
    icon.classList.add('animated');

    each($modal.querySelectorAll(".modal-body > div.col-md-6"), function(row, index){
        var p = {};

        p['display'] = index;
        p['type'] = row.dataset.type;
        p['label'] = row.querySelector('label').innerText.trim();
        p['helptext'] = row.getAttribute('title') || '';

        switch(p['type']){
            case 'int':
                p['value'] = parse_input(row.querySelector('input'));
                break;

            case 'string':
                p['value'] = parse_input(row.querySelector('input'));
                break;

            case 'bool':
                p['value'] = is_checked(row.querySelector('i.c_box'));
                p['label'] = row.querySelector('span._label').innerText;
                break;
        }
        config[row.dataset.key] = p;

    })

    var folder = $conf_modal.data("folder");
    var filename = $conf_modal.data("filename");
    config = JSON.stringify(config);

    $.post(url_base + "/ajax/save_plugin_conf", {"folder": folder,
                                                 "filename": filename,
                                                 "config": config
                                                 })
    .done(function(response){
        if(response['response'] == true){
            $.notify({message: response["message"]})
        } else {
            $.notify({message: response["error"]}, {type: "danger"});
        };
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        icon.classList.remove('mdi-circle');
        icon.classList.add('mdi-content-save');
        icon.classList.remove('animated');
    });
}

function _get_settings(){

    var settings = {};
    settings["added"] = {};
    settings["snatched"] = {};
    settings["finished"] = {};
    var blanks = false;


    each(['added', 'snatched', 'finished'], function(category){
        var enabled_plugins = [];
        var disabled_plugins = [];

        each(document.querySelectorAll(`form[data-category='${category}'] ul > li`), function(plugin){
            var name = plugin.dataset.name;

            if(is_checked(plugin.querySelector('i.c_box'))){
                settings[category][name] = [true];
                enabled_plugins.push(name);
            } else {
                settings[category][name] = [false];
                disabled_plugins.push(name);
            }

        });

        each(enabled_plugins.concat(disabled_plugins), function(name, index){
            settings[category][name].push(index);

        })
    });

    if(blanks == true){
        return false;
    };

    return {"Plugins": settings}
}
