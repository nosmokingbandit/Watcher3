$(document).ready(function(){
    $checkboxes = $("ul#movie_list > li > .c_box")

    echo.init({offsetVertical: 100,
               callback: function(element, op){
                   $(element).css("opacity", 1)
               }
    });

    $checkboxes.click(function(){
        $this = $(this);
        // turn on
        if( $this.attr("value") == "False" ){
            $this.attr("value", "True");
            $this.removeClass("mdi-checkbox-blank-outline").addClass("mdi-checkbox-marked");
        // turn off
        } else if ($this.attr("value") == "True" ){
            $this.attr("value", "False");
            $this.removeClass("mdi-checkbox-marked").addClass("mdi-checkbox-blank-outline");
        }
    });

    // Reset modal inner html after close
    $("div.modal").each(function(){
        var $this = $(this);
        var html = $this[0].innerHTML;
        $this.on("hidden.bs.modal", function(){
            $this.html(html);
        });
    });


});

function select_all(){
    $checkboxes.attr("value", "False").click();
}

function select_none(){
    $checkboxes.attr("value", "True").click();
}

function select_inverse(){
    $checkboxes.click();
}

function select_attrib(event, elem){
    event.preventDefault();
    var $this = $(elem);
    var key = $this.data("key");
    var value = $this.data("value");

    select_none();

    $("ul#movie_list > li").each(function(){
        var $this = $(this);
        if($this.find("span."+key).text() == value){
            $this.find("i.c_box").removeClass("mdi-checkbox-blank-outline").addClass("mdi-checkbox-marked");
        }
    })
}

function backlog_search(event, elem){
    // Preps call to _manager_request
    var movies = _selected_movies();

    if(movies.length == 0){
        $.notify({message: "No movies are selected."}, {type: "warning"})
        return
    }

    _manager_request($("div#modal_backlog_search"), "manager_backlog_search", {"movies": movies});
}

function refresh_metadata(event, elem){
    // Preps call to _manager_request
    var movies = _selected_movies();

    if(movies.length == 0){
        $.notify({message: "No movies are selected."}, {type: "warning"})
        return
    }

    _manager_request($("div#modal_metadata"), "manager_update_metadata", {"movies": movies});
}

function change_quality(event, elem){
    // Preps call to _manager_request
    var movies = _selected_movies();

    if(movies.length == 0){
        $.notify({message: "No movies are selected."}, {type: "warning"})
        return
    }

    var quality = $("div#modal_quality select#quality").val();

    _manager_request($("div#modal_quality"), "manager_change_quality", {"movies": movies, "quality": quality});
}

function reset_movies(event, elem){
    // Preps call to _manager_request
    var movies = _selected_movies();

    if(movies.length == 0){
        $.notify({message: "No movies are selected."}, {type: "warning"})
        return
    }

    var quality = $("div#modal_quality select#quality").val();

    _manager_request($("div#modal_reset"), "manager_reset_movies", {"movies": movies});
}

function remove_movies(event, elem){
    // Preps call to _manager_request
    var movies = _selected_movies();

    if(movies.length == 0){
        $.notify({message: "No movies are selected."}, {type: "warning"})
        return
    }

    _manager_request($("div#modal_remove"), "manager_remove_movies", {"movies": movies});
}


function _manager_request($modal, url, payload){
    /* Fires xhr ajax request for ajax/url_base with payload {movies: movies}
    modal: jquery object of open modal
    url: str url tail to be appended to 'url_base/ajax/<url>'
    payload: dict of POST data

    Hides modal body text and shows progress bar.
    Hides modal footer and removes action button

    Sends XHR ajax request to server with payload.

    On progress:
        Adjusts progress bar width %.
        Shows error table and appends any errors if neccesary.

    When done, shows modal footer.
    */

    var movie_count = payload["movies"].length;
    payload["movies"] = JSON.stringify(payload["movies"]);

    var $modal_p = $modal.find(".modal-body > p");
    $modal_p.empty();

    $modal.find(".modal-body > div.progress").slideDown();
    var $modal_footer = $modal.find('.modal-footer');
    $modal_footer.slideUp(500, function(){
        $modal_footer.find("a.btn")[1].remove();
    });

    $error_table = $modal.find(".modal-body > table");

    $progress_bar = $modal.find(".modal-body > div.progress > div.progress-bar");

    var last_response_len = false;
    $.ajax(url_base+"/ajax/"+url, {
        method: "POST",
        data: payload,
        xhrFields: {
            onprogress: function(e){
                var response_update;
                var response = e.currentTarget.response;
                if(last_response_len === false)
                {
                    response_update = response;
                    last_response_len = response.length;
                } else {
                    response_update = response.substring(last_response_len);
                    last_response_len = response.length;
                }

                response = JSON.parse(response_update);

                var progress = Math.round((parseInt(response["index"]) / movie_count) * 100);
                $progress_bar.width(progress + "%");
                $modal_p.text(`${response["index"]} / ${movie_count}`);

                if(response['response'] == false){
                    $error_table.show();
                    $error_table.find("tbody").append(`<tr>
                                                          <td> ${response['imdbid']} </td>
                                                          <td> ${response['error']} </td>
                                                      </tr>
                                                      `)
                }
            }
        }
    })
    .done(function(){
        $modal_footer.slideDown();
        $modal_p.html("Finished -- Refresh page to see changes.");
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    });

}

function _selected_movies(){
    // Returns list of dicts of selected movies.
    // IE [{imdbid: 'tt1234567', tmdbid: '123456'}, {imdbid: 'tt7654321', tmdbid: '654321'}]
    var movies = [];
    $checkboxes.each(function(){
        var $this = $(this);
        if($this.attr("value") == "True"){
            movies.push({"imdbid": $this.data("imdbid"),
                         "tmdbid": $this.data("tmdbid")
                         })
        }
    })
    return movies;
}
