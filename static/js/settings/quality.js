window.addEventListener("DOMContentLoaded", function(){
    profile_template = document.querySelector("template#profile_template").innerHTML;

    $profiles_form = $("form#profiles");

    each(document.querySelectorAll('i.mdi.radio'), function(r, i){
        r.addEventListener('click', function(){
            toggle_default()
        })
    })

});

function toggle_default(){
    var $i = event.target;
    if($i.getAttribute('value') == 'True'){
        return;
    } else {
        each(document.querySelectorAll('i.mdi.radio'), function(radio){
            radio.classList.remove('mdi-star');
            radio.classList.add('mdi-star-outline');
            radio.setAttribute('value', 'False');
        })
        $i.setAttribute('value', 'True');
        $i.classList.remove('mdi-star-outline');
        $i.classList.add('mdi-star');
    }
}

function edit_profile(event, button){
    event.preventDefault();
    $i = button.children[0];
    $contents = $(button).closest('div.quality_profile').find('div.profile_contents')
    if($i.classList.contains('mdi-chevron-down')){
        $i.classList.remove('mdi-chevron-down');
        $i.classList.add('mdi-chevron-up');
        $contents.slideDown();
    } else {
        $i.classList.remove('mdi-chevron-up');
        $i.classList.add('mdi-chevron-down');
        $contents.slideUp();
    }
}

function add_profile(event){
    event.preventDefault();
    var $new_profile = $(profile_template);
    $new_profile.find("i.c_box").each(function(){
        var $this = $(this);
        if(this.getAttribute("value") == "True"){
            this.classList.remove("mdi-checkbox-blank-outline");
            this.classList.add("mdi-checkbox-marked");
        }
    })
    $profiles_form.append($new_profile)
    init_sortables($new_profile.find('ul.sortable'))
    $new_profile.find('[data-toggle="tooltip"]').tooltip()
    $new_profile.find('i.mdi.radio').click(toggle_default);
}

function delete_profile(event, button){
    event.preventDefault();
    var $profile = $(button).closest('div.quality_profile');
    $profile.slideUp(500, function(){
        $profile.remove();
        $rads = $('i.mdi.radio');
        if($rads.filter('[value="true"]').length == 0){
            $rads[0].click();
        }
    });
}

function _get_settings(){
    var settings = {};
    settings["Profiles"] = {};
    settings["Aliases"] = {};
    settings["Sources"] = {};
    var blanks = false;

// QUALITY['PROFILES']
    var required_fields = ['name']

    each(document.querySelectorAll('div.quality_profile'), function(profile){
        quality = {};
        quality['Sources'] = {};

        // Name
        var name = profile.querySelector('input#name').value;
        if(!name){
            profile.querySelector('input#name').classList.add('border-danger');
            blanks = true;
            return
        }

        quality['default'] = is_checked(profile.querySelector('i.mdi.radio'));

        // Sources
        var enabled_sources = [];
        var disabled_sources = [];

        each(profile.querySelectorAll('ul.sources li'), function(source){
            var source_name = source.dataset.source;
            if(is_checked(source.querySelector('i.c_box'))){
                quality['Sources'][source_name] = [true];
                enabled_sources.push(source_name);
            } else {
                quality['Sources'][source_name] = [false];
                disabled_sources.push(source_name);
            }
        });

        var sorted_sources = enabled_sources.concat(disabled_sources);
        each(sorted_sources, function(src, index){
            quality['Sources'][src].push(index)
        });

        // Word Lists
        each(profile.querySelectorAll("div[data-sub-category='filters'] input"), function(input){
            quality[input.id] = input.value;
        });

        // Misc
        each(profile.querySelectorAll("div[data-sub-category='misc'] i.c_box"), function(checkbox){
            quality[checkbox.id] = is_checked(checkbox);
        });

        settings['Profiles'][name] = quality;
    });

    var default_set = false;
    each(Object.keys(settings['Profiles']), function(p){
        if(settings['Profiles'][p]['default']){
            default_set = true;
        }
    })
    if(!default_set){
        settings['Profiles'][Object.keys(settings['Profiles'])[0]]['default'] = true;
    }

// QUALITY['SOURCES']
    each(document.querySelectorAll("form[data-category='sources'] tbody > tr"), function(source){
        var src = source.id;

        settings['Sources'][src] = {};

        $min = source.querySelector("input[data-range='min']");
        $max = source.querySelector("input[data-range='max']");

        if($min.value == ""){
            $min.classList.add('border-danger');
            blanks = true;
        } else {
            settings["Sources"][src]["min"] = Math.max(parseInt($min.value), parseInt($min.getAttribute("min")));
        }

        if($max.value == ""){
            $max.classList.add('border-danger');
            blanks = true;
        } else {
            var max = Math.max(parseInt($max.value), parseInt($max.getAttribute("min")));
            if(max < settings["Sources"][src]["min"]){
                max = settings["Sources"][src]["min"];
            };
            settings["Sources"][src]["max"] = max;
        }
    });

// QUALITY['ALIASES']
    each(document.querySelectorAll("form[data-category='aliases'] input"), function(alias){
        if(alias.value == ""){
            alias.classList.add('border-danger');
            blanks = true;
            return
        }

        settings["Aliases"][alias.id] = alias.value.split(',').map(function(item){
            return item.trim();
        });
    });

    if(blanks == true){
        return false;
    };

    return {"Quality": settings}
}
