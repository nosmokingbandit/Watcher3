$(document).ready(function () {
    $profile_template = $($("textarea#profile_template")[0].innerText);

    // set default state for pseudo checkboxes
    $profile_template.find("i.c_box").each(function(){
        $this = $(this);
        if ($this.attr("value") == "True" ){
            $this.removeClass("fa-square-o")
            $this.addClass("fa-check-square");
        }
    });

    $profiles_form = $("form#profiles");
});

function add_profile(event){
    event.preventDefault();
    var $new_profile = $profile_template.clone().addClass("hidden");
    $new_profile.find("i.c_box").each(function(){
        var $this = $(this);
        if($this.attr("value") == "True"){
            $this.removeClass("mdi-checkbox-blank-outline").addClass("mdi-checkbox-marked");
        }
    })
    $profiles_form.append($new_profile)
    $new_profile.slideDown();
}

function delete_profile(event, elem){
    event.preventDefault();
    var $this = $(elem);
    var $profile = $this.closest('div.quality_profile');
    $profile.slideUp(500, function(){
        $(this).remove();
    })
}

function _get_settings(){

    var settings = {};
    settings["Profiles"] = {};
    settings["Aliases"] = {};
    settings["Sources"] = {};
    var blanks = false;

// QUALITY['PROFILES']
    var required_fields = ['name']

    $("div.quality_profile").each(function(i, elem){
        var $this = $(elem);

        // Name
        var profile = {};
        profile['Sources'] = {};

        var name = $this.find("input#name").val();

        if(!name){
            $this.find("input#name").addClass("empty")
            blanks = true;
            return;
        }

        // Sources
        var enabled_sources = [];
        var disabled_sources = [];
        $this.find("ul.sources li").each(function(i, elem){
            var $source = $(elem);
            var source_name = $source.data("source");

            if(is_checked($source.find("i.c_box"))){
                profile['Sources'][source_name] = [true];
                enabled_sources.push(source_name);
            } else {
                profile['Sources'][source_name] = [false];
                disabled_sources.push(source_name);
            }
        });

        var sorted_sources = $.merge(enabled_sources, disabled_sources);
        $.each(sorted_sources, function(i, source_name){
            profile['Sources'][source_name].push(i);
        });

        // Word Lists
        $this.find("div[data-sub-category='filters'] input").each(function(i, elem){
            var $elem = $(elem);
            profile[$elem.attr("id")] = $elem.val();
        });

        // Misc
        $this.find("div[data-sub-category='misc'] i.c_box").each(function(i, elem){
            var $this = $(elem)
            profile[$this.attr("id")] = is_checked($this);
        });

        settings['Profiles'][name] = profile;
    })

// QUALITY['SOURCES']
    $("form[data-category='sources'] tbody > tr").each(function(){
        var $this = $(this);
        var src = $this.attr("id");
        settings["Sources"][src] = {};

        $min = $this.find("input[data-range='min']");
        $max = $this.find("input[data-range='max']");

        if($min.val() == ""){
            $min.addClass("empty");
            blanks = true;
        } else {
            var min = parseInt($min.attr("min"));
            var val = Math.max(parseInt($min.val()), min);
            settings["Sources"][src]["min"] = val;
        }

        if($max.val() == ""){
            $max.addClass("empty");
            blanks = true;
        } else {
            var min = parseInt($max.attr("min"));
            var val = Math.max(parseInt($max.val()), min);
            if(val < settings["Sources"][src]["min"]){
                val = settings["Sources"][src]["min"];
            }
            settings["Sources"][src]["max"] = val;
        }
    });

// QUALITY['ALIASES']
    $("form[data-category='aliases'] :input").each(function(){
        var $this = $(this);
        if($this.val() == "" ){
            $this.addClass("empty");
            blanks = true;
        }

        settings["Aliases"][$this.attr("id")] = $this.val().split(',').map(function(item){
                                                                           return item.trim();
                                                                       });

    });

    if(blanks == true){
        return false;
    };
    return {"Quality": settings}
}
