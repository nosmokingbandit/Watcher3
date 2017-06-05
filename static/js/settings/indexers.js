$(document).ready(function () {
    indexer_template = $("textarea#new_indexer")[0].innerText;

});

function test_indexer(event, elem){
    event.preventDefault();
    $this = $(elem).find("i");
    var $tr = $this.closest('tr');

    var url = $tr.find("input[data-id='url']").val();

    if(!url){
        $.notify({message: "Enter an indexer URL."}, {type: "warning"})
        return
    }

    $this.removeClass("mdi-lan-pending").addClass("mdi-circle-outline animated");

    var api = $tr.find("input[data-id='api']").val();
    var mode = $this.closest("form").data("category");

    $.post(url_base + "/ajax/indexer_test", {"indexer": url,
                                             "apikey": api,
                                             "mode": mode})
    .done(function(r){
        response = JSON.parse(r);
        if(response["response"] == true){
            $.notify({message: `Connection Successful.`})
        } else {
            $.notify({message: `${response['error']}`}, {type: "danger"})
        }

        $this.removeClass("mdi-circle-outline animated").addClass("mdi-lan-pending");
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
