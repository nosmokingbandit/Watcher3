window.addEventListener("DOMContentLoaded", function(){
    current_page = 1;

    movie_count = parseInt(document.querySelector('meta[name="movie_count"]').content);
    cached_movies = Array(movie_count);

    per_page = 50;

    $page_select = document.querySelector("select#page_number");

    $page_select.addEventListener('change', function(event){
        current_page = parseInt(event.target.value);
        load_library(movie_sort_key, movie_sort_direction, current_page);
    });

    pages = Math.ceil(movie_count / per_page);
    document.querySelector("button#page_count").innerText = "/ "+pages;

    if(pages > 0){
        each(Array(pages), function(item, index){
            $page_select.innerHTML += `<option value="${index+1}">${index+1}</option>`;
        });
    } else {
        $page_select.innerHTML += `<option value="">0</option>`;
    }

    $page_select.value = '1';

    loading_library = false; // Indicates that a library ajax request is being executed

    $sort_direction_button = $("button#sort_direction > i");
    $sort_key_select = $("select#movie_sort_key");
    $movie_list = document.getElementById("movie_list");

    templates = {movie: document.querySelector("template#template_movie").innerHTML,
                 info: document.querySelector("template#template_movie_info").innerHTML,
                 delete: document.querySelector("template#template_delete").innerHTML,
                 release: document.querySelector("template#template_release").innerHTML
                }
    status_colors = {Finished: 'success',
                     Snatched: 'primary',
                     Found: 'info',
                     Available: 'info',
                     Wanted: 'warning',
                     Waiting: 'dark',
                     Bad: 'danger'
                     }

    var cookie = read_cookie();
    echo.init({offsetVertical: 100,
               callback: function(element, op){
                   $(element).css("opacity", 1)
               }
    });

/* Read cookie vars */
    movie_layout = (cookie["movie_layout"] || '').split(' ')[0] || "posters";
    movie_sort_direction = cookie["movie_sort_direction"] || "desc";
    movie_sort_key = cookie["movie_sort_key"] || "sort_title";
    if(movie_sort_key == 'status_key'){
        movie_sort_key = 'status'
    } else if(movie_sort_key == 'title') {
        movie_sort_key = 'sort_title'
    }
/* Set sort ui elements off cookie */
    $movie_list.classList = '';
    $movie_list.classList.add(movie_layout);
    document.querySelector(`div#movie_layout > div > button[data-layout="${movie_layout}"]`).classList.add("active");
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
    $("div#movie_layout > div > button").click(function(){
        var $this = $(this);
        if ($this.hasClass("active")) {
            return
        } else {
            var movie_layout = $this.attr("data-layout");
            $this.siblings().removeClass("active");
            $this.addClass("active");
            $movie_list.classList = '';
            $movie_list.classList.add(movie_layout);
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
    if(page == 0){
        return;
    }

    loading_library = true;

    $movie_list.innerHTML = '';

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
    each(movies, function(movie, index){
        var template = templates.movie;
        movie["url_base"] = url_base;

        movie["status_select"] = movie["status"]; // Keep "Disabled" for dropdown

        if(movie["status"] == "Disabled"){
            movie["status"] = "Finished";
        }

        movie['status_color'] = status_colors[movie['status']]

        movie["media_release_date"] = (movie["media_release_date"] || "Unannounced")

        if(!movie["poster"]){
            movie["poster"] = "missing_poster.jpg"
        }

        movie["status_translated"] = _(movie["status"])
        $item = format_template(template, movie);

        var score = Math.round(movie["score"]) / 2;
        if(score % 1 == 0.5){
            var i_half_star = Math.floor(score);
        }
        each($item.querySelectorAll("span.score > i.mdi"), function(star, index){
            if(index + 1 <= score){
                star.classList.replace("mdi-star-outline", "mdi-star");
            } else if(index == i_half_star){
                star.classList.replace("mdi-star-outline", "mdi-star-half");
            }

        });
        $item.dataset.movie = JSON.stringify(movie);
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
    $page_select.value = page;

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
            movie["table"] = `<li class="search_result list-group-item">
                                  <span>Nothing found yet. Next search sheduled for ${response["next"]}.</span>
                              </li>`;
        }
        var modal = format_template(templates.info, movie);
	movie['title_escape'] = movie['title'].replace(/'/g, "\\'");
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
            $movie_status.find("span#finished_file_badge").removeClass('hidden');
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
    each(results, function(result, index){
        if(result["freeleech"] >= 1){
            result['fl'] = `<span class="label label-default" title="Freeleech: ${result["freeleech"]}"><i class="mdi mdi-heart"></i></span>`
        } else if(result["freeleech"] > 0 && result["freeleech"] < 1 ){
            result['fl'] = `<span class="label label-default" title="Freeleech: ${result["freeleech"]}"><i class="mdi mdi-heart-half-full"></i></span>`
        } else {
            result['fl'] = "";
        }

        result["translated_status"] = _(result["status"]);
        result['status_color'] = status_colors[result['status']]
        rows += format_template(templates.release, result).outerHTML;
    });

    return rows
}

function manual_search(event, button, imdbid){
    $i = button.querySelector('i.mdi');

    $i.classList.replace("mdi-magnify", "mdi-circle");
    $i.classList.add("animated");

    var $search_results_table = document.getElementById("search_results_table");
    var orig_maxHeight = getComputedStyle($search_results_table).maxHeight;
    $search_results_table.style.overflowY = 'hidden';
    $search_results_table.style.maxHeight = '0px';

    var table = "";

    $.post(url_base + "/ajax/search", {"imdbid":imdbid})
    .done(function(response){
        if(response["response"] == true && response["results"].length > 0){
            $search_results_table.innerHTML = _results_table(response["results"]);
        } else if(response["response"] == true && response["results"].length == 0){
            table = `<div class="search_result list-group-item">
                         <span>Nothing found yet. Next search sheduled for ${response["next"]}.</span>
                     </div>`;
            $search_results_table.innerHTML = table;
        } else {
            $.notify({message: response["error"]}, {type: "danger"});
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
        $search_results_table.style.maxHeight = orig_maxHeight;
        $i.classList.replace("mdi-circle", "mdi-magnify");
        $i.classList.remove('animated');
        $search_results_table.style.overflowY = 'scroll';
    });
}

function update_metadata(event, elem, imdbid, tmdbid){
    event.preventDefault();

    var $i = $(elem).find("i.mdi");
    $i.removeClass("mdi-tag-text-outline").addClass("mdi-circle animated");

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
        $i.removeClass("mdi-circle animated").addClass("mdi-tag-text-outline");
    });
}

function remove_movie(event, elem, imdbid){
    event.preventDefault();

    var movie = $movie_status.data("movie");

    var modal = format_template(templates.delete, movie);
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
                $movie_list.querySelector(`li[data-imdbid="${imdbid}"]`).outerHTML = '';
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
    $i.removeClass("mdi-download").addClass("mdi-circle animated");

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
            update_release_status(guid, 'Snatched');
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        }
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $i.removeClass("mdi-circle animated").addClass("mdi-download");
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

    $i.removeClass("mdi-cancel").addClass("mdi-circle animated");

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
            update_release_status(guid, 'Bad')
        } else {
            $.notify({message: response["error"]}, {type: "danger"})
        };
    })
    .fail(function(data){
        var err = data.status + " " + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $i.removeClass("mdi-circle animated").addClass("mdi-cancel");
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

    var label = document.querySelector(`ul#movie_list > li[data-imdbid="${imdbid}"] span.status`)

    if(label){
        label.textContent = status;
        label.classList = `badge badge-${status_colors[status]} status`;
    }

    var $status_label = $movie_list.querySelector(`li[data-imdbid="${imdbid}"] span.status`)
    $status_label.classList.replace($status_label.innerText, status);
    $status_label.innerText = status;
    return
}

function update_release_status(guid, status){
    /* Updates status label for search result
    guid: str guid of target release
    status: str status to update label to
    */

    var label = document.querySelector(`li.search_result[data-guid="${guid}"] span.status`)

    if(label){
        label.textContent = status;
        label.classList = `badge badge-${status_colors[status]} status`;
    }

}

function go_similar(event, elem, tmdbid, title){
    if (tmdbid == ""){
        return false;
    }

    window.location.href = url_base+'/sugg_similar?tmdbid=' + tmdbid;

}
