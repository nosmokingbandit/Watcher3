$(document).ready(function() {
    var url_base = $("meta[name='url_base']").attr("content");

    $("#search_input").keyup(function(event){
        if(event.keyCode == 13){
            $("#search_button").click();
        }
    });

    // Sends request to search ajax handler
    $("#search_button").click(function(e) {
        var movie_results_dict = {};
        if ( $("input[name='search_term']").val() == "" ){
            return false;
        }

        // if it is open, hide it first. makes it pretty
        if ( $("#database_results").css("display") == "block" ){
            $("#database_results").hide();
            $("#movie_list").empty();
        }

        $('#thinker').fadeIn();

        $.post(url_base + "/ajax/search_tmdb", {
            "search_term": $("input[name='search_term']").val()
        })

        .done(function(r) {
            if (r != ''){

                movie_results_dict = JSON.parse(r);
                results = JSON.parse(r);
                var movie_list = $("#movie_list")
                // move this to a py template or just have the post function return the html ?
                $.each(results, function(ind, dict){
                    if(dict['poster_path'] != null){
                        img_url = "http://image.tmdb.org/t/p/w300" + dict['poster_path']
                    } else {
                        img_url = url_base + "/static/images/missing_poster.jpg"
                    }

                    $('<li>', {class: 'movie'}).attr('data', JSON.stringify(dict)).append(
                        $("<span>", {class:'quickadd'}).append(
                            $("<span>", {class: 'quickadd_text'}).text('Quick-Add'),
                            $("<i>", {class: 'fa fa-plus button_add'})
                            ),
                        $('<img>', {src:img_url}),
                        dict['title'],' ',dict['release_date'].slice(0,4)
                    ).appendTo(movie_list)
                });
            }

            $("#database_results").fadeIn();
            $('#thinker').fadeOut();
        });

        e.preventDefault();
    });

// quickadd buttons
    $("ul#movie_list").on("mouseenter", "span.quickadd", function(){
        $(this).children("span.quickadd_text").stop(true, true).animate(
            {width: 'toggle'}
        )
    });

    $("ul#movie_list").on("mouseleave", "span.quickadd", function(){
        $(this).children("span.quickadd_text").stop(true, true).animate(
            {width: 'toggle'}
        )
    });

    $("ul#movie_list").on("click", "span.quickadd", function(){
        $this = $(this);
        imdbid = $this.attr('imdbid');

        $icon = $this.children("i");
        $icon.removeClass('fa-plus');
        $icon.addClass('fa-circle faa-burst animated');

        data = $this.parent().attr('data')
        data['quality'] = 'Default'

        $.post(url_base + "/ajax/add_wanted_movie", {"data":data})
        .done(function(r){
            response = JSON.parse(r)

            $icon.removeClass('fa-circle faa-burst animated');
            $icon.addClass('fa-plus');

            if(response['response'] == true){
                toastr.success(response['message']);
            } else {
                toastr.error(response['error']);
            };
        })
    });

// applies add movie overlay
    $('div#database_results').on('click', 'img', function(){
        $('div#overlay').fadeIn();

        data = $(this).parent().attr('data')

        $.post(url_base + "/ajax/movie_info_popup", {"data": data})
            .done(function(html){
                $('div#info_pop_up').html(html).slideDown();
            });
    });

    $('body').on('click' ,'div#overlay', function(){
        $(this).fadeOut();
        $('div#info_pop_up').slideUp();
        $("div#info_pop_up").empty();
    });
});
