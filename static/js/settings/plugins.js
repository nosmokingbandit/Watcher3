$(document).ready(function(){
    template_config = $("textarea#template_config")[0].innerText

});

function edit_plugin_conf(event, elem, folder, filename){
    event.preventDefault()
    var config_file;

    $.post(url_base + "/ajax/get_plugin_conf", {"folder": folder, "conf": filename})
    .done(function(config_file){
        if(!config_file){
            $.notify({message: "Unable to read plugin config."}, {type: "danger"})
            return false
        }

        var conf_table = "";

        $.each(config_file, function(k, v){
            conf_table += `
                            <div class="col-md-6">
                               <label>${k}</label>
                               <input type="text" class="form-control" data-key="${k}" value="${v}">
                            </div>
                          `
        })

        var template_dictionary = {"name": filename.replace(".conf", ""),
                                   "folder": folder,
                                   "filename": filename,
                                   "config": conf_table
                                   }

        $(format_template(template_config, template_dictionary)).modal('show');

    })
    .fail(function(response){
        $.notify({message: "Unable to read plugin config."}, {type: "danger"})
        return
    });

    return
}

function save_plugin_conf(event, elem){
    event.preventDefault()
    var $this = $(elem);
    var original_content = $this.text();
    var $modal = $this.closest(".modal-content").find(".modal-body");

    var config = {};
    $modal.find("input").each(function(i, elem){
        $input = $(elem);
        config[$input.data("key")] = $input.val();
    })

    var folder = $modal.data("folder");
    var filename = $modal.data("filename");
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
    });

}

function _get_settings(){

    var settings = {};
    settings["added"] = {};
    settings["snatched"] = {};
    settings["finished"] = {};
    var blanks = false;

// PLUGINS['ADDED']
    var enabled_plugins = [];
    var disabled_plugins = [];

    $("form[data-category='added'] ul > li").each(function(i, elem){
        var $plugin = $(elem);
        var plugin_name = $plugin.data("name");

        if(is_checked($plugin.find("i.c_box"))){
            settings['added'][plugin_name] = [true];
            enabled_plugins.push(plugin_name);
        } else {
            settings['added'][plugin_name] = [false];
            disabled_plugins.push(plugin_name);
        }
    });

    var sorted_plugins = $.merge(enabled_plugins, disabled_plugins);
    $.each(sorted_plugins, function(i, plugin_name){
        settings['added'][plugin_name].push(i);
    });

// PLUGINS['SNATCHED']
    var enabled_plugins = [];
    var disabled_plugins = [];

    $("form[data-category='snatched'] ul > li").each(function(i, elem){
        var $plugin = $(elem);
        var plugin_name = $plugin.data("name");

        if(is_checked($plugin.find("i.c_box"))){
            settings['snatched'][plugin_name] = [true];
            enabled_plugins.push(plugin_name);
        } else {
            settings['snatched'][plugin_name] = [false];
            disabled_plugins.push(plugin_name);
        }
    });

    var sorted_plugins = $.merge(enabled_plugins, disabled_plugins);
    $.each(sorted_plugins, function(i, plugin_name){
        settings['snatched'][plugin_name].push(i);
    });

// PLUGINS['FINISHED']
    var enabled_plugins = [];
    var disabled_plugins = [];

    $("form[data-category='finished'] ul > li").each(function(i, elem){
        var $plugin = $(elem);
        var plugin_name = $plugin.data("name");

        if(is_checked($plugin.find("i.c_box"))){
            settings['finished'][plugin_name] = [true];
            enabled_plugins.push(plugin_name);
        } else {
            settings['finished'][plugin_name] = [false];
            disabled_plugins.push(plugin_name);
        }
    });

    var sorted_plugins = $.merge(enabled_plugins, disabled_plugins);
    $.each(sorted_plugins, function(i, plugin_name){
        settings['finished'][plugin_name].push(i);
    });

    if(blanks == true){
        return false;
    };

    return {"Plugins": settings}
}
