$(document).ready(function () {
    each(document.querySelectorAll('input[type="time"]'), function(input){
        var hr = input.dataset.hour.toString().padStart(2, 0);
        var min = input.dataset.minute.toString().padStart(2, 0);
        input.value = hr + ':' + min;
    })
});

function _get_settings(){

    var settings = {};
    settings["Watchlists"] = {};
    settings["Watchlists"]['Traktlists'] = {};
    var blanks = false;

// SEARCH
    var required_fields = ['rsssyncfrequency', 'waitdays', 'mintorrentseeds', 'freeleechpoints', 'retention']

    each(document.querySelectorAll("form[data-category='search'] i.c_box"), function(checkbox){
        settings[checkbox.id] = is_checked(checkbox);
    })

    if(settings['skipwait']){
        required_fields.push("skipwaitweeks")
    }
    if(settings['keepsearching']){
        required_fields.push("keepsearchingdays", "keepsearchingscore")
    }

    each(document.querySelector("form[data-category='search']").querySelectorAll('input, select'), function(input){
        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return
        }
        settings[input.id] = parse_input(input);
    })

// SERVER['WATCHLISTS']
    required_fields = []

    each(document.querySelectorAll("form[data-category='watchlists'] i.c_box"), function(checkbox){
        if(checkbox.dataset['subCategory'] == 'traktlist'){
            settings['Watchlists']['Traktlists'][checkbox.id] = is_checked(checkbox);
        } else {
            settings['Watchlists'][checkbox.id] = is_checked(checkbox);
        }
    })

    if(settings["Watchlists"]['imdbsync']){
        required_fields.push("imdbcsv", "imdbfrequency")
    }
    if(settings["Watchlists"]['popularmoviessync']){
        required_fields.push("popularmoviestime")
    }
    if(settings["Watchlists"]['traktsync']){
        required_fields.push("traktfrequency", "traktscore", "traktlength")
    }


    each(document.querySelector("form[data-category='watchlists']").querySelectorAll('input, select'), function(input){
        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return
        }
        if(input.id == 'popularmoviestime'){
            var [hour, min] = input.value.split(":").map(function(item){
                return parseInt(item);
            });
            settings['Watchlists']['popularmovieshour'] = hour;
            settings['Watchlists']['popularmoviesmin'] = min;
        } else if(input.id == "imdbcsv"){
            settings["Watchlists"]["imdbcsv"] = input.value.split(',').map(function(item){
                                                                               return item.trim();
                                                                           });
        } else {
            settings['Watchlists'][input.id] = parse_input(input);
        }
    })

    if(blanks == true){
        return false;
    };

    return {"Search": settings}
}
