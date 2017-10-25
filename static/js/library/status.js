$(document).ready(function(){
    current_page = 1;

    movie_count = parseInt($("meta[name='movie_count']").attr("content"));
    cached_movies = Array(movie_count);

    per_page = 50;

    $page_select = $("select#page_number");
    $page_select.on("change", function(){
        current_page = parseInt(this.value);
        load_library(movie_sort_key, movie_sort_direction, current_page);
    });

    pages = Math.ceil(movie_count / per_page);
    $("a#page_count").text("/ "+pages)

    each(Array(pages), function(item, index){
        $page_select.prepend(`<option value="${index+1}">${index+1}</option>`);
    });
    $page_select.find("option")[0].setAttribute("selected", true);

    loading_library = false; // Indicates that a library ajax request is being executed

    $sort_direction_button = $("a#sort_direction > i");
    $sort_key_select = $("select#movie_sort_key");
    $movie_list = $("ul#movie_list");

    movie_template = $("textarea#template_movie")[0].innerText
    info_template = $("textarea#template_movie_info")[0].innerText;
    delete_template = $("textarea#template_delete")[0].innerText;

    var cookie = read_cookie();
    echo.init({offsetVertical: 100,
               callback: function(element, op){
                   $(element).css("opacity", 1)
               }
    });

/* Read cookie vars */
    movie_layout = cookie["movie_layout"] || "posters";
    movie_sort_direction = cookie["movie_sort_direction"] || "desc";
    movie_sort_key = cookie["movie_sort_key"] || "sort_title";
    if(movie_sort_key == 'status_key'){
        movie_sort_key = 'status'
    } else if(movie_sort_key == 'title') {
        movie_sort_key = 'sort_title'
    }
/* Set sort ui elements off cookie */
    $movie_list.removeClass().addClass(movie_layout);
    $(`div#movie_layout > div > a[data-layout="${movie_layout}"]`).addClass("active");
    echo.render();

    if (movie_sort_direction == "asc") {
        $sort_direction_button.addClass("mdi-sort-ascending");
    } else {
        $sort_direction_button.addClass("mdi-sort-descending");
    }

    $sort_key_select.find(`option[value=${movie_sort_key}]`).attr("selected", "true")

/* Finish by loading page 1 */
    load_library(movie_sort_key, movie_sort_direction, 1)

/* Toolbar action bindings
    /* Movie sort key */
	$("select#movie_sort_key").change(function(event){
        if(loading_library){
            event.preventDefault();
            return false
        }
		movie_sort_key = $(this).find("option:selected").val();

        var reset_cache = false;
        for(i=0; i < cached_movies.length; i++){
            if(cached_movies[i] === undefined){
                reset_cache = true;
                break
            }
        }

        if(reset_cache){
            cached_movies = Array(movie_count);
        } else {
            sort_movie_cache(movie_sort_key);
        }

		set_cookie("movie_sort_key", movie_sort_key);

        load_library(movie_sort_key, movie_sort_direction, current_page);
	});

    /* Movie sort direction */
    // See fn switch_sort_direction()

    /* Movie layout style */
    $("div#movie_layout > div > a").click(function(){
        var $this = $(this);
        if ($this.hasClass("active")) {
            return
        } else {
            var movie_layout = $this.attr("data-layout");
            $this.siblings().removeClass("active");
            $this.addClass("active");
            $movie_list.removeClass().addClass(movie_layout);
            set_cookie('movie_layout', movie_layout)
            echo.render();
        }
    });

    // toggle checkbox status on click
    $("body").on("click", "i.c_box", function(){
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

});

exp_date = new Date();
exp_date.setFullYear(exp_date.getFullYear() + 10);
exp_date = exp_date.toUTCString();

jQuery.fn.justtext = function(){
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
        value = decodeURIComponent(cookiearray[i].split("=")[1]);
        cookie_obj[key] = value
    }
    return cookie_obj
}

function set_cookie(k, v){
    /* Helper method to set cookies
    k (str): cookie key
    v (str): cookie value

    Constructs and sets cookie in browser

    Returns cookie string
    */

    var c = `${k}=${encodeURIComponent(v)};path=/;expires=${exp_date}`;

    document.cookie = c;

    return
}

function sort_movie_cache(key){
    if (movie_sort_direction == "desc") {
        var forward = 1;
        var backward = -1;
    } else {
        var forward = -1;
        var backward = 1;
    }

    cached_movies.sort(function(a, b){
        if(a[key] > b[key]){
            return forward
        } else if(a[key] < b[key]){
            return backward
        } else {
            return 0
        }
    });
}

function load_library(sort_key, sort_direction, page){
    /* Loads library into DOM
    sort_key: str value with which to sort movies
    sort_direction: str [asc, desc] direction to sort movies
    page: int page number

    Clears movies from dom and loads new page.
    Checks if all movies are cached and loads them. If not cached requests movies from server.
    */

    loading_library = true;

    $movie_list.empty();

    var offset = (page * per_page) - per_page;

    var use_cache = true;
    var cached_page = cached_movies.slice(offset, offset + per_page)

    for(i=0; i < cached_page.length; i++){
        if(cached_page[i] === undefined){
            use_cache = false;
            break
        }
    }

    if(use_cache) {
        _render_library(cached_page);
        loading_library = false;
    } else {
        $.post(url_base+"/ajax/library", {
            "sort_key": sort_key,
            "sort_direction": sort_direction,
            "limit": per_page,
            "offset": offset
        })
        .done(function(response){
            Array.prototype.splice.apply(cached_movies, [offset, response.length].concat(response))
            _render_library(response);

        })
        .fail(function(data){
            var err = data.status + ' ' + data.statusText
            $.notify({message: err}, {type: "danger", delay: 0});
        })
        .always(function(){
            loading_library = false;
        });
    }
}

function _render_library(movies){
    // Renders movies list items after loading page
    $.each(movies, function(i, movie){
        var template = movie_template;
        movie["url_base"] = url_base;

        movie["status_select"] = movie["status"]; // Keep "Disabled" for dropdown

        if(movie["status"] == "Disabled"){
            movie["status"] = "Finished";
        }

        movie["media_release_date"] = (movie["media_release_date"] || "Unannounced")

        if (movie["poster"]){
            movie["poster"] = "posters/" + movie["poster"]
        } else {
            movie["poster"] = "static/images/missing_poster.jpg"
        }


        movie["status_translated"] = _(movie["status"])
        $item = $(format_template(template, movie));

        var score = Math.round(movie["score"]) / 2;
        if(score % 1 == 0.5){
            var i_half_star = Math.floor(score);
        }
        $item.find("span.score > i.mdi").each(function(i, elem){
            if(i+1 <= score){
                $(elem).removeClass("mdi-star-outline").addClass("mdi-star");
            } else if(i == i_half_star){
                $(elem).removeClass("mdi-star-outline").addClass("mdi-star-half");
            }

        });
        $item.data("movie", movie);
        $movie_list.append($item)
    });

    echo.init({offsetVertical: 100,
        callback: function(element, op){
            $(element).css("opacity", 1)
        }
    });
}

function change_page(event, elem, page){
    // page: int page #
    // Fails if loading_library is true
    // Constructs then forwards request to load_library
    event.preventDefault();

    if(loading_library){
        return false;
    }

    var $btn = $(elem);

    $page_buttons.removeClass("active");
    $btn.addClass("active");

    load_library(movie_sort_key, movie_sort_direction, page)

    current_page = page;
}

function change_page_sequential(event, direction){
    // direction: int direction and count of pages to move [-1, 1]
    event.preventDefault();
    if(loading_library){
        return false;
    }

    page = current_page + direction;

    if(page < 1 || page > pages){
        return false
    }
    $page_select.val(page.toString());

    load_library(movie_sort_key, movie_sort_direction, page)
    current_page = page;
}

function switch_sort_direction(event, elem){
    // Change sort direction of movie list
    if(loading_library){
        event.preventDefault();
        return false
    }

    if ($sort_direction_button.hasClass("mdi-sort-ascending")){
        $sort_direction_button.removeClass("mdi-sort-ascending").addClass("mdi-sort-descending");
        movie_sort_direction = "desc";
    } else {
        $sort_direction_button.removeClass("mdi-sort-descending").addClass("mdi-sort-ascending");
        movie_sort_direction = "asc";
    }

    set_cookie("movie_sort_direction", movie_sort_direction);

    cached_movies.reverse();
    reversed_pages = [];

    load_library(movie_sort_key, movie_sort_direction, current_page);
}

function open_info_modal(event, elem){
    // Generate and show movie info modal
    event.preventDefault();

    var movie = $(elem).data("movie");
    if(movie["origin"] === null){
        movie["origin"] = ""
    }

    var search_results = {};
    var results_table = "";
    $.post(url_base + "/ajax/get_search_results", {
        "imdbid": movie["imdbid"],
        "quality": movie["quality"]
    })
    .done(function(response){
        if(response["response"] == true){
            movie["table"] = _results_table(response["results"]);
        } else {
            movie["table"] = `<div class="search_result">
                                  <span>Nothing found yet. Next search sheduled for ${response["next"]}.</span>
                              </div>`;
        }

        var modal = format_template(info_template, movie);
        $movie_status = $(modal);

        $movie_status.data("movie", movie);
        $movie_status.find("select#movie_quality > option[value='"+movie["quality"]+"']").attr("selected", true)
        $status_select = $movie_status.find("select#movie_status");

        if(movie["status_select"] == "Disabled"){
             $status_select.find("option[value='Disabled']").attr("selected", true)
        } else {
            $status_select.find("option[value='Automatic']").attr("selected", true)
        }

        if(movie["status"] == "Finished" || movie["status"] == "Disabled"){
            var label = `<span class="label label-success">
                            File: ${movie["finished_file"]}
                         </span>`
            $movie_status.find("div.modal-header").append($(label));
        }

        $movie_status.modal("show");
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
}

function _results_table(results){
    /* Generate search results table for modal
    results: list of dicts of result info
    */

    rows = "";
    $.each(results, function(i, result){
        if(result["freeleech"] >= 1){
            var fl = `<span class="label label-default" title="Freeleech: ${result["freeleech"]}"><i class="mdi mdi-heart"></i></span>`
        } else if(result["freeleech"] > 0 && result["freeleech"] < 1 ){
            var fl = `<span class="label label-default" title="Freeleech: ${result["freeleech"]}"><i class="mdi mdi-heart-half-full"></i></span>`
        } else {
            var fl = "";
        }

        result["translated_status"] = _(result["status"]);

        rows += `<div class="search_result">
                    <div class="col-md-12">
                        <span class="title" title="${result['title']}">
                            ${result["title"]}
                        </span>
                    </div>
                    <div class="result_info col-md-6">
                        <span class="label status ${result["status"]}" title="Status">${result["translated_status"]}</span>
                        <span class="label label-default" title="Link Type">${result["type"]}</span>
                        <span class="label label-default" title="Indexer">${result["indexer"]}</span>
                        <span class="label label-default" title="Size">${result["size"]}</span>
                        <span class="label label-default" title="Score">${result["score"]}</span>
                        ${fl}
                    </div>
                    <div class="result_actions col-md-6 btn-group btn-group-justified">
                        <a class="btn btn-sm btn-default" href="${result['info_link']}" target="_blank" rel="noopener" title="Visit Indexer">
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
    .done(function(response){
        if(response["response"] == true && response["results"].length > 0){
            $search_results_table.html(_results_table(response["results"]));
            $search_results_table.slideDown();

        } else if(response["response"] == true && response["results"].length == 0){
            table = `<div class="search_result">
                         <span>Nothing found yet. Next search sheduled for ${response["next"]}.</span>
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
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
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
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]})
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $i.removeClass("mdi-circle-outline animated").addClass("mdi-tag-text-outline");
    });
}

function remove_movie(event, elem, imdbid){
    event.preventDefault();

    var movie = $movie_status.data("movie");

    var modal = format_template(delete_template, movie);
    $delete = $(modal);

    if(!movie["finished_file"]){
        $delete.find("div#delete_file").hide();
    }

    $delete.modal("show");
    $movie_status.css("opacity", 0);
    $delete.on('hide.bs.modal', function(){
        $movie_status.css("opacity", 1);
    });
}

function _remove_movie(event, elem, imdbid){
    /* Removes movie from library
    imdbid: str imdb id# of movie to remove
    */

    var $this = $(elem);
    var movie = $movie_status.data("movie");

    if($("div#delete_file > i.c_box").attr("value") == "True"){
        var delete_file = true;
    } else {
        var delete_file = false;
    }

    function __remove_from_library(imdbid){
        $.post(url_base + "/ajax/remove_movie", {"imdbid":imdbid})
        .done(function(response){
            if(response["response"] == true){
                $.notify({message: response["message"]});
                $movie_list.find(`li[data-imdbid="${imdbid}"]`).remove();
                $movie_status.modal("hide");
            } else {
                $.notify({message: response["error"]}, {type: "danger"})
            }

            var index = cached_movies.map(function(e){ return e.imdbid; }).indexOf(imdbid);
            cached_movies.splice(index, 1);

            $movie_status.modal("hide");

        })
        .fail(function(data){
            var err = data.status + " " + data.statusText
            $.notify({message: err}, {type: "danger", delay: 0});
        });
    };

    if(delete_file){
        $.post(url_base + "/ajax/delete_movie_file", {"imdbid": imdbid})
        .done(function(response){
            if(response["response"] == true){
                $.notify({message: response["message"]}, {type: "success"});
            } else {
                $.notify({message: response["error"]}, {type: "danger"});
            }
        })
        .fail(function(data){
            var err = data.status + " " + data.statusText;
            $.notify({message: err}, {type: "danger", delay: 0});
        })
        .always(function(){
            $delete.modal("hide");
            // Makes sure the file removal is done after file removal
            __remove_from_library(imdbid);
        });
    } else {
        $delete.modal("hide");
        __remove_from_library(imdbid);
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
    .done(function(response){
        if(response["response"]){
            $.notify({message: response["message"]})
            update_movie_status(imdbid, response["status"]);
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
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
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]})

            update_movie_status(imdbid, "Snatched");

            var $label = $this.closest("div.search_result").find("span.status");
            $label.removeClass($label.text()).addClass("Snatched").text("Snatched");
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
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
    .done(function(response){

        if(response["movie_status"]){
            update_movie_status(imdbid, response["movie_status"]);
        }

        if (response["response"] == true){
            $.notify({message: response["message"]})
            var $label = $this.closest("div.search_result").find("span.status");
            $label.removeClass("Available Snatched Finished").addClass("Bad").text(_("Bad"));
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        };
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
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
