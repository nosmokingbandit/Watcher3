$(document).ready(function() {
    details_template = $("textarea#details_template")[0].innerText;
    var $search_input = $("div#search_bar input");
    var $search_button = $("div#search_bar #search_button");
    var $movie_list = $("ul#movies");
    var item_template = $("textarea#movie_template").text();

    $search_input.keyup(function(event){
        if(event.keyCode == 13){
            $search_button.click();
        }
    });

    // Sends request to search ajax handler
    $search_button.click(function(event) {
        event.preventDefault();
        var movie_results_dict = {};
        var search_term = $search_input.val();

        if (search_term == ""){
            return false;
        }

        if($movie_list.css("display") != "none"){
            $movie_list.hide();
            $movie_list.empty();
        }

        $("#thinker").fadeIn();

        $.post(url_base + "/ajax/search_tmdb", {
            "search_term": search_term
        })
        .done(function(r) {
            if (r){
                var results = JSON.parse(r);
                $.each(results, function(ind, movie){
                    if(movie["poster_path"] != null){
                        movie["img_url"] = "http://image.tmdb.org/t/p/w300" + movie["poster_path"]
                    } else {
                        movie["img_url"] = url_base + "/static/images/missing_poster.jpg"
                    }

                    movie["year"] = (movie["release_date"] || "N/A").slice(0,4)

                    var template_dictionary = {"img_url": movie["img_url"],
                                               "title": movie["title"],
                                               "year": movie["year"]
                                               }

                    var li = format_template(item_template, template_dictionary);
                    var $li = $(li);
                    $li.data("movie", movie);
                    $movie_list.append($li)
                });
            }

            $movie_list.css("display", "flex").hide().fadeIn();
            $("#thinker").fadeOut();
        });
    });
});

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
    .done(function(r){
        response = JSON.parse(r)

        $add_button.html(original_contents);

        if(response["response"] == true){
            $.notify({message: `${title} added to library.`})
        } else {
            $.notify({message: `${response['error']}`}, {type: "warning"})
        }
    })
}

function show_details(event, elem){
    event.preventDefault();
    var $this = $(elem);
    movie = $this.closest("li").data("movie");

    movie["trailer"] = "";

    $.post(url_base + "/ajax/get_trailer", {"title": movie["title"],
                                            "year": movie["title"]
                                            })
    .done(function(r){
        if(r){
            movie["trailer"] = `https://www.youtube.com/embed/${r}?&showinfo=0`;
        }
        var modal = format_template(details_template, movie)

        $modal = $(modal);
        $modal.data("movie", movie);
        $modal.modal("show");
        $modal.on('hidden.bs.modal', function(){
            $modal.remove();
        });
    })

}