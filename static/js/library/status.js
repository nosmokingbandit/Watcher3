$(document).ready(function() {
    modal_template = $("textarea#template_movie_info")[0].innerText;
    $sort_direction_i = $("a#sort_direction > i");
    $movie_list = $("ul#movie_list");

    var cookie = read_cookie();
    echo.init({offsetVertical: 100,
               callback: function(element, op){
                   $(element).css("opacity", 1)
               }
    });

/* Read cookie vars */
    movie_layout = cookie["movie_layout"] || "posters";
    movie_sort_direction = cookie["movie_sort_direction"] || "desc";
    movie_sort_key = cookie["movie_sort_key"] || "title";

/* Movie sort direction */
    if (movie_sort_direction == "asc") {
        $sort_direction_i.addClass("mdi-sort-ascending");
    } else {
        $sort_direction_i.addClass("mdi-sort-descending");
    }
	sortOrder(movie_sort_key, movie_sort_direction, $("ul#movie_list"), "li")

/* Movie layout style */
    $movie_list.removeClass().addClass(movie_layout);
    $(`div#movie_layout > a[data-layout="${movie_layout}"]`).addClass("active");
    echo.render();

    $("div#movie_layout > a").click(function() {
        var $this = $(this);
        if ($this.hasClass("active")) {
            return
        } else {
            movie_layout = $this.attr("data-layout");
            $this.siblings().removeClass("active");
            $this.addClass("active");
            $movie_list.removeClass().addClass(movie_layout);
            document.cookie = `movie_layout=${movie_layout};path=/`;
            echo.render();
        }
    });

/* Movie sort key */
	$("select#movie_sort_key").change(function(){
		movie_sort_key = $(this).find("option:selected").val()

		document.cookie = "movie_sort_key=" + movie_sort_key + ";path=/";

		sortOrder(movie_sort_key, movie_sort_direction, $("ul#movie_list"), "li")
	});

});

var exp_date = new Date();
exp_date.setFullYear(exp_date.getFullYear() + 10);
exp_date = exp_date.toUTCString();

jQuery.fn.justtext = function() {
    return $(this).clone()
        .children()
        .remove()
        .end()
        .text();
};

function read_cookie() {
    /* Read document cookie
    Returns dict
    */
    var dcookie = document.cookie;
    cookie_obj = {};
    cookiearray = dcookie.split("; ");

    for (var i = 0; i < cookiearray.length; i++) {
        key = cookiearray[i].split("=")[0];
        value = cookiearray[i].split("=")[1];
        cookie_obj[key] = value
    }
    return cookie_obj
}

function sortOrder(order, direction, $parent, children) {
    /* Change order by which to sort movie list
    order: str class of element with which to sort by
    direction: str up or down for asc / desc
    $parent: jquery object in which to find children to sort
    children: str type of children element to sort (li, span, etc)
    each child must have a span with class "order". text is taken from span to sort by.
    */

    if (direction == "desc") {
        var forward = 1;
        var backward = -1;
    } else {
        var forward = -1;
        var backward = 1;
    }

    var $element = $parent.children(children);

    $element.sort(function(a, b) {
        var an = $(a).find("span." + order).justtext(),
            bn = $(b).find("span." + order).justtext();

        if (an > bn)
            return forward;
        if (an < bn)
            return backward;

        return 0;
    });

    $element.detach().appendTo($parent);
}

function sort_direction(event, elem){
    // Change sort direction of movie list

    if ($sort_direction_i.hasClass("mdi-sort-ascending")){
        $sort_direction_i.removeClass("mdi-sort-ascending").addClass("mdi-sort-descending");
        movie_sort_direction = "desc";
    } else {
        $sort_direction_i.removeClass("mdi-sort-descending").addClass("mdi-sort-ascending");
        movie_sort_direction = "asc";
    }
    document.cookie = `movie_sort_direction=${movie_sort_direction};path=/`;
    sortOrder(movie_sort_key, movie_sort_direction, $("ul#movie_list"), "li");
    echo.render();
}

function open_info_modal(event, elem){
    // Generate and show movie info modal

    event.preventDefault();

    var movie = JSON.parse($(elem).find("span.movie").text());
    movie["poster"] = url_base + "/static/images/posters/" + movie["imdbid"] + ".jpg"

    var search_results = {};
    var results_table = "";
    $.post(url_base + "/ajax/get_search_results", {
        "imdbid": movie["imdbid"],
        "quality": movie["quality"]
    })
    .done(function(r) {
        var response = JSON.parse(r);
        if(response["response"] == true){
            movie["table"] = _results_table(response["results"]);
        } else {
            movie["table"] = `<div class="search_result">
                                  <span class="col-md-12">Nothing found yet. Next search sheduled for ${response["next"]}.</span>
                              </div>`;
        }

        var modal = format_template(modal_template, movie);
        $movie_status = $(modal);

        $movie_status.data("title", movie["title"]);
        $movie_status.find("select#movie_quality > option[value='"+movie["quality"]+"']").attr("selected", true)
        $status_select = $movie_status.find("select#movie_status");
        if(movie["status"] == "Disabled"){
             $status_select.find("option[value='Disabled']").attr("selected", true)
        } else {
            $status_select.find("option[value='Automatic']").attr("selected", true)
        }

        $movie_status.modal("show");
    });
}

function _results_table(results){
    /* Generate search results table for modal
    results: list of dicts of result info
    */

    rows = "";
    $.each(results, function(i, result){
        rows += `<div class="search_result">
                    <div class="col-md-12">
                        <span class="title" title="${result['title']}">
                            ${result["title"]}
                        </span>
                    </div>
                    <div class="result_info col-md-6 btn-group btn-group-justified">
                        <span class="btn btn-sm status ${result["status"]}">${result["status"]}</span>
                        <span class="btn btn-sm">${result["type"]}</span>
                        <span class="btn btn-sm">${result["indexer"]}</span>
                        <span class="btn btn-sm">${result["size"]}</span>
                    </div>
                    <div class="result_actions col-md-6 btn-group btn-group-justified">
                        <a class="btn btn-sm btn-default" href="${result['info_link']}" target="_blank" title="Visit Indexer">
                            <i class="mdi mdi-information-outline"></i>
                        </a>
                        <a class="btn btn-sm btn-default" title="Download" onclick="manual_download(event, this, '${result["guid"]}', '${result["type"]}', '${result["imdbid"]}')">
                            <i class="mdi mdi-download"></i>
                        </a>
                        <a class="btn btn-sm btn-default" onclick="mark_bad(event, this, '${result["guid"]}', '${result["imdbid"]}')" title="Mark release as Bad">
                            <i class="mdi mdi-cancel"></i>
                        </a>
                    </div>
                </div>
                `
    })
    return rows
}

function manual_search(event, elem, imdbid){
    $i = $(elem).find("i.mdi");

    $i.removeClass("mdi-magnify").addClass("mdi-circle-outline animated");

    var $search_results_table = $("div#search_results_table");
    $search_results_table.slideUp();

    var table = "";


    $.post(url_base + "/ajax/search", {"imdbid":imdbid})
    .done(function(r){
        response = JSON.parse(r);
        if(response["response"] == true && response["results"].length > 0){
            $search_results_table.html(_results_table(response["results"]));
            $search_results_table.slideDown();

        } else if(response["response"] == true && response["results"].length == 0){
            table = `<div class="search_result">
                         <span class="col-md-12">Nothing found yet. Next search sheduled for ${response["next"]}.</span>
                     </div>`;
            $search_results_table.html(table);
            $search_results_table.slideDown();

        } else {
            $.notify({message: response["error"]}, {type: "danger"});
            $search_results_table.slideDown();
        }

        if(response["movie_status"]){
            update_movie_status(imdbid, response["movie_status"]);
        }

        $i.removeClass("mdi-circle-outline animated").addClass("mdi-magnify");
    });
}

function update_metadata(event, elem, imdbid, tmdbid){
    event.preventDefault();

    var $i = $(elem).find("i.mdi");
    $i.removeClass("mdi-tag-text-outline").addClass("mdi-circle-outline animated");

    $.post(url_base + "/ajax/update_metadata", {
        "imdbid": imdbid,
        "tmdbid": tmdbid
    })
    .done(function(r){
        response = JSON.parse(r);
        if(response["response"] == true){
            $.notify({message: response["message"]})
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }
        $i.removeClass("mdi-circle-outline animated").addClass("mdi-tag-text-outline");
    });


}

function remove_movie(event, elem, imdbid){
    /* Removes movie from library
    imdbid: str imdb id# of movie to remove
    */

    event.preventDefault();
    var $this = $(elem);
    var title = $movie_status.data("title");

    if($this.data("confirm") !== true){
        $this.removeClass("btn-default").addClass("btn-danger").data("confirm", true).text("Confirm Delete?");
    } else if($this.data("confirm") === true){
        $.post(url_base + "/ajax/remove_movie", {"imdbid":imdbid})
        .done(function(r){
            response = JSON.parse(r)
            if(response["response"] == true){
                $.notify({message: `${title} removed from library.`})
                $movie_list.find(`li[data-imdbid="${imdbid}"]`).remove();
                $movie_status.modal("hide");
            } else {
                var message = `${title} could not be removed. Check logs for more information.`;
                $.notify({message: "Unable to read plugin config."}, {type: "danger"})
            }
        });
    }
}

function update_movie_options(event, elem, imdbid){
    var $this = $(this);
    var $i = $this.find("i");

    var quality = $("select#movie_quality").val();
    var status = $("select#movie_status").val();

    $.post(url_base+"/ajax/update_movie_options", {
        "quality": quality,
        "status": status,
        "imdbid": imdbid
    })
    .done(function(r){
        response = JSON.parse(r);
        if(response["response"]){
            $.notify({message: `${imdbid} updated.`})
            update_movie_status(imdbid, response["status"]);
        } else {
            $.notify({message: `Unable to update ${imdbid}.`}, {type: "danger"})
        }

    })
}

function manual_download(event, elem, guid, kind, imdbid){
    event.preventDefault();

    var $this = $(elem);
    var $i = $this.find("i.mdi");
    $i.removeClass("mdi-download").addClass("mdi-circle-outline animated");

    var year = $movie_status.find("div.modal-header span.year").text();

    $.post(url_base + "/ajax/manual_download", {
        "year": year,
        "guid": guid,
        "kind": kind
    })
    .done(function(r){
        response = JSON.parse(r);

        if(response["response"] == true){
            $.notify({message: response["message"]})

            update_movie_status(imdbid, "Snatched");

            var $label = $this.closest("div.search_result").find("span.status");
            $label.removeClass($label.text()).addClass("Snatched").text("Snatched");
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }

        $i.removeClass("mdi-circle-outline animated").addClass("mdi-download");
    });
}

function mark_bad(event, elem, guid, imdbid){
    /* Mark search result as Bad
    guid: str absolute guid of download
    imdbid: str imdb id# of movie
    */
    event.preventDefault();
    $this = $(elem);

    var $i = $this.find("i.mdi");

    $i.removeClass("mdi-cancel").addClass("mdi-circle-outline animated");

    $.post(url_base + "/ajax/mark_bad", {
        "guid": guid,
        "imdbid": imdbid,
        "cancel_download": true
    })
    .done(function(r){
        var response = JSON.parse(r);

        if(response["movie_status"]){
            update_movie_status(imdbid, response["movie_status"]);
        }

        if (response["response"] == true){
            $.notify({message: `Marked release as Bad.`})
            var $label = $this.closest("div.search_result").find("span.status");
            $label.removeClass($label.text()).addClass("Bad").text("Bad");

        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        };

        $i.removeClass("mdi-circle-outline animated").addClass("mdi-cancel");
    });
}

function update_movie_status(imdbid, status){
    /* Updates movie in Status list to status
    imdbid: str imdb id# of movie to change
    status: str new status of movie
    */
    if(status == "Disabled"){
        status = "Finished"
    }

    var $status_label = $movie_list.find(`li[data-imdbid="${imdbid}"] span.status`)
    $status_label.removeClass($status_label.text());
    $status_label.addClass(status).text(status);
    return
}

function update_result_status($child, status){
    /* Updates status label for search result
    $child: jquery object of any element inside the div.search_result of the target
    status: str status to update label to
    */

    var $status_label = $child.closest("div.search_result").find("span.status");
    $status_label.removeClass($status_label.text());
    $status_label.addClass(status).text(status);

}