$(document).ready(function(){
    template_config = $("textarea#template_config")[0].innerText

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
            $this = $(this);
            if ($this.attr("value") == "True" ){
                $this.removeClass("mdi-checkbox-blank-outline").addClass("mdi-checkbox-marked");
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

function save_plugin_conf(event, elem){
    event.preventDefault()
    var $this = $(elem);
    var original_content = $this.text();

    var config = {"Config Version": 2};
    $conf_modal.find(".modal-body > div.col-md-6").each(function(i, elem){
        var p = {};
        p["display"] = i;
        var $this = $(elem);
        p["type"] = $this.data("type");
        p["label"] = $this.find("label")[0].innerText.trim();
        p["helptext"] = $this.attr("title") || "";

        if(p["type"] == "int"){
            var $input = $this.find("input");
            var name = $input.data("key");
            p["max"] = parseInt($input.attr("max"));
            p["max"] = (isNaN(p["max"]) ? "" : p["max"]);
            p["min"] = parseInt($input.attr("min"));
            p["min"] = (isNaN(p["min"]) ? "" : p["min"]);
            var v = parseInt($input.val());
            if(p["max"] && v > p["max"]){
                p["value"] = p["max"];
            }
            else if(p["min"] && v < p["min"]){
                p["value"] = p["min"];
            }
            else {
                p["value"] = v;
            }
        }
        else if(p["type"] == "string"){
            var $input = $this.find("input");
            var name = $input.data("key");
            p["value"] = $input.val();
        }
        else if(p["type"] == "bool"){
            var $i = $this.find("i.c_box");
            var name = $i.data("key");
            p["value"] = is_checked($i);
            p["label"] = $this.find("span._label")[0].innerText
        }
        else {
            return;
        }

        config[name] = p;
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
