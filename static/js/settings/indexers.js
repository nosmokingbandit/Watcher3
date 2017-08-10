$(document).ready(function () {
    indexer_template = $("textarea#new_indexer")[0].innerText;

});

function test_indexer(event, elem){
    event.preventDefault();
    var orig_oc = elem.getAttribute("onClick");
    elem.removeAttribute("onClick");

    $this = $(elem).find("i");
    var $tr = $this.closest('tr');

    var url = $tr.find("input[data-id='url']").val();

    if(!url){
        return
    }

    $this.removeClass("mdi-lan-pending").addClass("mdi-circle-outline animated");

    var api = $tr.find("input[data-id='api']").val();
    var mode = $this.closest("form").data("category");

    $.post(url_base + "/ajax/indexer_test", {"indexer": url,
                                             "apikey": api,
                                             "mode": mode})
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]})
        } else {
            $.notify({message: response['error']}, {type: "danger"})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $this.removeClass("mdi-circle-outline animated").addClass("mdi-lan-pending");
        elem.setAttribute("onClick", orig_oc);
    });
}

function add_indexer(event, mode){
    event.preventDefault();
    $(`form[data-category="${mode}"] tbody`).append(indexer_template);
}

function remove_indexer(event, elem){
    var $this = $(elem);
    $this.closest("tr").fadeOut(500, function(){$(this).remove()});
}

function _get_settings(){

    var settings = {};
    settings["NewzNab"] = {};
    settings["TorzNab"] = {};
    settings["Torrent"] = {};
    var blanks = false;

// INDEXERS['NEWZNAB']
    var required_fields = [];

    $("form[data-category='newznab'] tbody > tr").each(function(i, elem){
        var $this = $(elem);

        var $url = $this.find("input[data-id='url']");
        var url = $url.val();
        var $api = $this.find("input[data-id='api']");
        var api = $api.val();

        if(api && !url){
            $url.addClass('empty');
            blanks = true;
            return false;
        }
        else if(!api && !url){
            return false;
        }
        else {
            enabled = is_checked($this.find("i.c_box"));
            settings["NewzNab"][i] = [url, api, enabled];
        }
    });

// INDEXERS['TORZNAB']
    var required_fields = [];

    $("form[data-category='torznab'] tbody > tr").each(function(i, elem){
        var $this = $(elem);

        var $url = $this.find("input[data-id='url']");
        var url = $url.val();
        var $api = $this.find("input[data-id='api']");
        var api = $api.val();

        if(api && !url){
            $url.addClass('empty');
            blanks = true;
            return false;
        }
        else if(!api && !url){
            return false;
        }
        else {
            enabled = is_checked($this.find("i.c_box"));
            settings["TorzNab"][i] = [url, api, enabled];
        }
    });

// INDEXERS['TORRENT']
    var required_fields = [];

    $("form[data-category='torrent'] i.c_box").each(function(i, elem){
        var $this = $(elem);

        settings["Torrent"][$this.attr("id")] = is_checked($this);
    });

    if(blanks == true){
        return false;
    };

    return {"Indexers": settings}
}
