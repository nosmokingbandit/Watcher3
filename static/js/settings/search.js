$(document).ready(function () {
    $("input[type='time']").each(function(i, elem){
        var $this = $(elem);
        var hr = $this.data("hour").toString().padStart(2, 0);
        var min = $this.data("minute").toString().padStart(2, 0);
        $this.attr("value", hr + ":" + min);
    })

});

function _get_settings(){

    var settings = {};
    settings["Watchlists"] = {};
    settings["Watchlists"]['Traktlists'] = {};
    var blanks = false;

// SEARCH
    var required_fields = ['rsssyncfrequency', 'waitdays', 'mintorrentseeds', 'freeleechpoints', 'retention']

    $("form[data-category='search'] i.c_box").each(function(){
        var $this = $(this);
        settings[$this.attr("id")] = is_checked($this);
    });

    if(settings['skipwait']){
        required_fields.push("skipwaitweeks")
    }
    if(settings['keepsearching']){
        required_fields.push("keepsearchingdays", "keepsearchingscore")
    }

    $("form[data-category='search'] :input:not(button)").each(function(){
        var $this = $(this);
        if($this.val() == "" && required_fields.includes($this.attr("id"))){
            $this.addClass("empty");
            blanks = true;
        }

        if($this.attr("type") == "number"){
            var min = parseInt($this.attr("min"));
            var val = Math.max(parseInt($this.val()), min);
            settings[$this.attr("id")] = val || min;
        }
        else{
            settings[$this.attr("id")] = $this.val();
        }
    });

// SERVER['WATCHLISTS']
    required_fields = []

    $("form[data-category='watchlists'] i.c_box").each(function(){
        var $this = $(this);
        if($this.data("sub-category") == "traktlist"){
            settings["Watchlists"]["Traktlists"][$this.attr("id")] = is_checked($this);
        } else {
            settings["Watchlists"][$this.attr("id")] = is_checked($this);
        }
    });

    if(settings["Watchlists"]['imdbsync']){
        required_fields.push("imdbrss", "imdbfrequency")
    }
    if(settings["Watchlists"]['popularmoviessync']){
        required_fields.push("popularmoviestime")
    }
    if(settings["Watchlists"]['traktsync']){
        required_fields.push("traktfrequency", "traktscore", "traktlength")
    }

    $("form[data-category='watchlists'] :input:not(button)").each(function(){
        var $this = $(this);
        if($this.val() == "" && required_fields.includes($this.attr("id"))){
            $this.addClass("empty");
            blanks = true;
        }

        if($this.attr("id") == "popularmoviestime"){
            var [hour, min] = $this.val().split(":").map(function(item){
                                                             return parseInt(item);
                                                         });

            settings["Watchlists"]["popularmovieshour"] = hour;
            settings["Watchlists"]["popularmoviesmin"] = min;
        }
        else if($this.attr("type") == "number"){
            var min = parseInt($this.attr("min"));
            var val = Math.max(parseInt($this.val()), min);
            settings["Watchlists"][$this.attr("id")] = val || min;
        }
        else if($this.attr("id") == "imdbrss"){
            settings["Watchlists"]["imdbrss"] = $this.val().split(',').map(function(item){
                                                                               return item.trim();
                                                                           });
        }
        else {
            settings["Watchlists"][$this.attr("id")] = $this.val();
        }
    });

    if(blanks == true){
        return false;
    };

    return {"Search": settings}
}