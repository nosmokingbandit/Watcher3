$(document).ready(function(){
    details_template = $("textarea#details_template")[0].innerText;
    $search_input = $("div#search_bar input");
    $search_button = $("div#search_bar #search_button");
    $movie_list = $("ul#movies");
    $thinker = $("div#thinker");
    item_template = $("textarea#movie_template").text();

    $search_input.keyup(function(event){
        if(event.keyCode == 13){
            search_tmdb(event, $search_button[0]);
        }
    });
});

function search_tmdb(event, elem){
    // Sends term to ajax handler
    event.preventDefault();
    var orig_oc = elem.getAttribute("onClick");
    elem.removeAttribute("onClick");

    var movie_results_dict = {};
    var search_term = $search_input.val();

    if (search_term == ""){
        return false;
    }

    if($movie_list.css("display") != "none"){
        $movie_list.hide();
        $movie_list.empty();
    }

    $thinker.fadeIn();

    $.post(url_base + "/ajax/search_tmdb", {
        "search_term": search_term
    })
    .done(function(results){
        $.each(results, function(ind, movie){
            if(movie["poster_path"] != null){
                var poster_path = movie['poster_url'] = "http://image.tmdb.org/t/p/w300" + movie["poster_path"]
            } else {
                var poster_path = movie['poster_url'] = url_base + "/static/images/missing_poster.jpg"
            }

            movie["year"] = (movie["release_date"] || "N/A").slice(0,4)

            var template_dictionary = {"img_url": poster_path,
                                        "title": movie["title"],
                                        "year": movie["year"]
                                        }

            var li = format_template(item_template, template_dictionary);
            var $li = $(li);
            $li.data("movie", movie);
            $movie_list.append($li)
        });

        $movie_list.css("display", "flex").hide().fadeIn();
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        elem.setAttribute("onClick", orig_oc);
        $thinker.fadeOut();
    });
}

function add_movie(event, elem, quality_profile, modal=false){
    $this = $(elem);
    var $add_button = $this.closest("div.btn-group").find("span.dropdown-toggle");
    var original_contents = $add_button[0].innerHTML;
    $add_button.html("&nbsp;<i class='mdi mdi-circle-outline animated'></i>")

    if(modal){
        var data = $modal.data("movie");
    } else {
        var data = $this.closest("li.movie").data("movie");
    }
    data['quality'] = quality_profile;
    var title = data['title']

    $.post(url_base + "/ajax/add_wanted_movie", {"data":JSON.stringify(data)})
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]})
        } else {
            $.notify({message: response['error']}, {type: "warning"})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    })
    .always(function(){
        $add_button.html(original_contents);
    });
}

function show_details(event, elem){
    event.preventDefault();
    var $this = $(elem);
    movie = $this.closest("li").data("movie");

    movie["trailer"] = "";

    var modal = format_template(details_template, movie)
    $modal = $(modal);
    $modal.data("movie", movie);
    $modal.modal("show");
    $modal.on('hidden.bs.modal', function(){
        $modal.remove();
    });

    $.post(url_base + "/ajax/get_trailer", {"title": movie["title"],
                                            "year": movie["title"]
                                            })
    .done(function(r){
        if(r){
            $modal.find("iframe#trailer").attr("src", `https://www.youtube.com/embed/${r}?&showinfo=0`);
        }
    });
}
