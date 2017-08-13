$(document).ready(function(){
    $("label[for='plex_csv']").click(function(){
        $("input#plex_csv_file").removeClass("empty");
    })

});

function read_csv(event, elem){
    event.preventDefault();

    var file_input = document.getElementById('plex_csv');
    if(file_input.files.length == 0){
        $('input#plex_csv_file').addClass("empty");
        return false
    }

    var post_data = new FormData();
    post_data.append('file_input', file_input.files[0])


    $("div#csv_upload").slideUp();
    $("a#read_csv").slideUp();
    $progress.slideDown();

    $.ajax({
        url: url_base+'/ajax/upload_plex_csv',
        type: 'POST',
        data: post_data,
        processData: false,
        contentType: false
    })
    .done(function(response){
        $progress_bar.width("100%");
        $progress.slideUp();

        if(response["response"] !== true){
            $("div#csv_upload").slideDown();
            $("a#read_csv").slideDown();
            $.notify({message: response["error"]}, {type: "warning"})
            return false
        }

        if(response["complete"].length + response["incomplete"].length == 0){
            $("div#no_new_movies").slideDown();
            return false
        }

        var $complete_div = $("div#complete_movies");
        var $complete_table = $("div#complete_movies table tbody");
        var $incomplete_div = $("div#incomplete_movies");
        var $incomplete_table = $("div#incomplete_movies table tbody");

        $.each(response["complete"], function(index, movie){
            if(movie['imdbid']){
                id = movie['imdbid']
            } else {
                id = movie['tmdbid']
            }
            var select = $(source_select);
            select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);
            var $row = $(`<tr>
                            <td>
                                <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                            </td>
                            <td class="file_path" data-original="${movie['file']}">
                                ${movie["file"]}
                            </td>
                            <td>
                                ${movie["title"]}
                            </td>
                            <td>
                                ${movie["imdbid"] || movie["tmdbid"]}
                            </td>
                            <td class="resolution">
                                ${select[0].outerHTML}
                            </td>
                        </tr>`)
            $row.data("movie", movie);
            $complete_table.append($row);
            $complete_div.show();
        });

        $.each(response["incomplete"], function(index, movie){
            var select = $(source_select);
            select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);
            var $row = $(`<tr>
                            <td>
                                <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                            </td>
                            <td class="file_path" data-original="${movie['file']}">
                                ${movie["file"]}
                            </td>
                            <td>
                                ${movie["title"]}
                            </td>
                            <td>
                                <input type="text" class="incomplete_imdbid form-control" placeholder="tt0000000" value="${movie['imdbid']}"/>
                            </td>
                            <td class="resolution">
                                ${select[0].outerHTML}
                            </td>
                        </tr>`)
            $row.data("movie", movie);
            $incomplete_table.append($row);
            $incomplete_div.show();
        });

        $("div#remote_map").slideDown();
        $("a#import_library").slideDown();
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
}

function apply_remote(event){
    event.preventDefault();
    var local = $("input#local_path").val();
    var remote = $("input#remote_path").val();
    $("div#complete_movies table > tbody > tr td.file_path").each(function(i, elem){
        $elem = $(elem);
        $elem.text($elem.text().replace(remote, local));
    })
    $("div#incomplete_movies table > tbody > tr td.file_path").each(function(i, elem){
        $elem = $(elem);
        $elem.text($elem.text().replace(remote, local));
    })
};

function reset_remote(event){
    event.preventDefault();
    $("div#complete_movies table > tbody > tr td.file_path").each(function(i, elem){
        var $elem = $(elem);
        $elem.text($elem.data("original"));
    })
    $("div#incomplete_movies table > tbody > tr td.file_path").each(function(i, elem){
        var $elem = $(elem);
        $elem.text($elem.data("original"));
    })
};

function import_library(event, elem){
    event.preventDefault();

    var movies = [];
    var corrected_movies = [];

    $("div#complete_movies table > tbody > tr ").each(function(i, row){
        var $row = $(row);
        if(!is_checked($row.find("i.c_box"))){
            return
        }

        movie = $row.data("movie");
        movie["finished_file"] = $row.find("td.file_path").text().trim();
        movie["resolution"] = $row.find("select.source_select").val();
        movies.push(movie);
    });

    var blanks = false;
    $("div#incomplete_movies table > tbody > tr ").each(function(i, row){
        var $row = $(row);
        if(!is_checked($row.find("i.c_box"))){
            return
        }

        movie = $row.data("movie");
        movie["imdbid"] = $row.find("input.incomplete_imdbid").val();

        if(!movie["imdbid"]){
            blanks = true;
            $row.find("input.incomplete_imdbid").addClass("empty");
            return
        }

        movie["finished_file"] = $row.find("td.file_path").text().trim();
        movie["resolution"] = $row.find("select.source_select").val();
        corrected_movies.push(movie);
    });

    if(blanks){
        $.notify({message: _("Fill highlighted fields or disable movie to continue.")}, {type: "warning"});
        return false;
    }

    $("div#remote_map").slideUp();
    $("div#complete_movies").slideUp();
    $("div#incomplete_movies").slideUp();
    $("a#import_library").slideUp();
    $progress_bar.width("0%");
    $progress.slideDown();

    var $success = $("div#import_success");
    var $success_table = $("div#import_success table > tbody");
    var $error = $("div#import_error");
    var $error_table = $("div#import_error table > tbody")

    var last_response_len = false;
    $.ajax(url_base + '/ajax/import_plex_csv', {
        method: "POST",
        data: {"movies": JSON.stringify(movies),
               "corrected_movies": JSON.stringify(corrected_movies)
               },
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

                var progress_text = `${r['progress'][0]} / ${r['progress'][1]} ${r['title']}.`;
                var progress_percent = Math.round(parseInt(r['progress'][0]) / parseInt(r['progress'][1]) * 100);


                $progress_text.text(progress_text);

                $progress_bar.width(progress_percent + "%")
                if(r['response'] == true){
                    $success.slideDown()
                    var row = `<tr>
                                    <td>${r['title']}</td>
                                    <td>${r['imdbid']}</td>
                                </tr>`
                    $success_table.append(row)
                } else {
                    $error.slideDown()
                    var row = `<tr>
                                    <td>${r['title']}</td>
                                    <td>${r['error']}</td>
                                </tr>`
                    $error_table.append(row)
                }

                if(progress_percent == 100){
                    $progress_text.text(_("Finishing Import."));
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

