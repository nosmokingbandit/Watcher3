$(document).ready(function () {
    mapping_template = $("textarea#template_mapping")[0].innerText;
    $mapping_table = $(`form[data-category="remote_mapping"] tbody`);
});

function add_mapping(event, elem){
    event.preventDefault();
    $mapping_table.append(mapping_template);
}

function remove_mapping(event, elem){
    var $this = $(elem);
    $this.closest("tr").fadeOut(500, function(){$(this).remove()});
}

function _get_settings(){
    var settings = {};
    settings["RemoteMapping"] = {};
    settings["Scanner"] = {};
    var blanks = false;

// POSTPROCESSING
    var required_fields = [];

    $("form[data-category='postprocessing'] i.c_box").each(function(){
        var $this = $(this);
        settings[$this.attr("id")] = is_checked($this);
    });

    if(settings['renamerenabled']){
        required_fields.push('renamerstring')
    }

    if(settings['moverenabled']){
        required_fields.push('moverpath')
    }

    if(settings['recyclebinenabled']){
        required_fields.push('recyclebindirectory')
    }

    $("form[data-category='postprocessing'] :input:not(button)").each(function(){

        if(this.tagName == 'SELECT'){
            settings[this.id] = this.options[this.selectedIndex].value;
        } else {
            var $this = $(this);

            if($this.val() == "" && required_fields.includes($this.attr("id"))){
                $this.addClass("empty");
                blanks = true;
                return;
            }
            settings[$this.attr("id")] = $this.val();
        }
    });

// POSTPROCESSING["SCANNER"]
    $("form[data-category='scanner'] i.c_box").each(function(){
        var $this = $(this);
        settings["Scanner"][$this.attr("id")] = is_checked($this);
    });

    if(settings["Scanner"]["enabled"] == true){
        required_fields.push("directory", "interval");
    }

    $("form[data-category='scanner'] :input:not(button)").each(function(){
        var $this = $(this);

        if($this.val() == "" && required_fields.includes($this.attr("id"))){
            $this.addClass("empty");
            blanks = true;
            return;
        }

        if($this.attr("type") == "number"){
            var min = parseInt($this.attr("min"));
            var val = Math.max(parseInt($this.val()), min);
            settings["Scanner"][$this.attr("id")] = val || min;
        }
        else{
            settings["Scanner"][$this.attr("id")] = $this.val();
        }
    });

// POSTPROCESSING["REMOTEMAPPING"]
    $("form[data-category='remote_mapping'] tbody > tr").each(function(){
        $this = $(this);

        var $remote = $this.find("input[data-id='remote']");
        var remote = $remote.val();
        var $local = $this.find("input[data-id='local']");
        var local = $local.val();

        if(!remote && !local){
            return true;
        }
        else if(remote && !local){
            $local.addClass("empty");
        }
        else if(local && !remote){
            $remote.addClass("empty");
        }
        else{
            settings['RemoteMapping'][remote] = local;
        }
    });

    if(blanks == true){
        return false;
    };

    return {'Postprocessing': settings}
}
