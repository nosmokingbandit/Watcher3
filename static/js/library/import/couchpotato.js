function scan_library(event, elem){
    event.preventDefault();

    var address = $("input#address").val();
    if(!address){
        $("input#address").addClass("empty");
        return false
    }
    var port = $("input#port").val();
    if(!port){
        $("input#port").addClass("empty");
        return false
    }
    var apikey = $("input#apikey").val();
    if(!apikey){
        $("input#port").addClass("empty");
        return false
    }

    var url = address + ":" + port

    $("div#server_info").slideUp();
    $("a#scan_library").slideUp();
    $progress.slideDown();


    $.post(url_base+"/ajax/get_cp_movies", {
        "url": url,
        "apikey": apikey
    })
    .done(function(response){
        $progress_bar.width("100%");
        $progress.slideUp();

        if(response["response"] !== true){
            $("div#server_info").slideDown();
            $("a#scan_library").slideDown();
            $.notify({message: response["error"]}, {type: "warning"})
            return false
        }

        if(response["movies"].length == 0){
            $("div#no_new_movies").slideDown();
            return false
        }

        var $finished_div =  $("div#finished_movies");
        var $finished_table = $("div#finished_movies table tbody");
        var $wanted_div = $("div#wanted_movies");
        var $wanted_table = $("div#wanted_movies table tbody");

        $.each(response["movies"], function(index, movie){
            var select = $(source_select);
            select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);

            if(movie["status"] === "Disabled"){
                var $row = $(`<tr>
                                <td>
                                    <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                                </td>
                                <td>
                                    ${movie["title"]}
                                </td>
                                <td>
                                    ${movie["imdbid"]}
                                </td>
                                <td class="resolution">
                                    ${select[0].outerHTML}
                                </td>
                            </tr>`)
                $row.data("movie", movie);
                $finished_table.append($row)
                $finished_div.show();
            } else {
                var $row = $(`<tr>
                                <td>
                                    <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                                </td>
                                <td>
                                    ${movie["title"]}
                                </td>
                                <td>
                                    ${movie["imdbid"]}
                                </td>
                                <td class="profile">
                                    ${quality_select}
                                </td>
                            </tr>`)
                $row.data("movie", movie);
                $wanted_table.append($row)
                $wanted_div.show();
            }
        });

        $("a#import_library").slideDown();
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });

}

function import_library(event, elem){
    event.preventDefault();

    var wanted_movies = [];
    var finished_movies = [];

    $("div#wanted_movies").slideUp();
    $("div#finished_movies").slideUp();
    $("a#import_library").slideUp();
    $progress_bar.width("0%");
    $progress.slideDown();


    $("div#finished_movies table > tbody > tr ").each(function(i, row){
        var $row = $(row);
        if(!is_checked($row.find("i.c_box"))){
            return
        }

        movie = $row.data("movie");
        movie["resolution"] = $row.find("select.source_select").val();
        finished_movies.push(movie);
    });

    $("div#wanted_movies table > tbody > tr ").each(function(i, row){
        var $row = $(row);
        if(!is_checked($row.find("i.c_box"))){
            return
        }

        movie = $row.data("movie");
        movie["quality"] = $row.find("select.quality_select").val();
        wanted_movies.push(movie);
    });

    var $success = $("div#import_success");
    var $success_table = $("div#import_success table > tbody");
    var $error = $("div#import_error");
    var $error_table = $("div#import_error table > tbody")

    var last_response_len = false;
    $.ajax(url_base + '/ajax/import_cp_movies', {
        method: "POST",
        data: {"wanted": JSON.stringify(wanted_movies), "finished": JSON.stringify(finished_movies)},
        xhrFields: {
            onprogress: function(e){
                var response_update;
                var response = e.currentTarget.response;
                if(last_response_len === false){
                    response_update = response;
                    last_response_len = response.length;
                } else {
                    response_update = response.substring(last_response_len);
                    last_response_len = response.length;
                }
                var r = JSON.parse(response_update);

                var progress_text = `${r['progress'][0]} / ${r['progress'][1]} ${r['movie']['title']}.`;
                var progress_percent = Math.round(parseInt(r['progress'][0]) / parseInt(r['progress'][1]) * 100);

                $progress_text.text(progress_text);

                $progress_bar.width(progress_percent + "%")
                if(r['response'] === true){
                    $success.slideDown()
                    var row = `<tr>
                                    <td>${r['movie']['title']}</td>
                                    <td>${r['movie']['imdbid']}</td>
                                </tr>`
                    $success_table.append(row)
                } else {
                    $error.slideDown()
                    var row = `<tr>
                                    <td>${r['movie']['title']}</td>
                                    <td>${r['error']}</td>
                                </tr>`
                    $error_table.append(row)
                }
            }
        }
    })
    .done(function(data){
        $progress.slideUp();
        $progress_text.slideUp();
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    })
    .always(function(){
        $('a#import_return').slideDown();
    });
}
