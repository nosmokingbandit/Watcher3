$(document).ready(function(){
    $dir_input = $("input#directory_input");

    $modal_current_dir = $("div#modal_current_dir");
    $modal_file_list = $("ul#modal_file_list");

    $modal_file_list.on("click", "li", function(){
        $this = $(this);
        var path = $this.text();
        $.post(url_base+'/ajax/list_files', {
            "current_dir": $modal_current_dir.text(),
            "move_dir": path
        })
        .done(function(response){
            if(response['error']){
                $.notify({message: response['error']}, {type: "danger"})
            } else {
                $modal_current_dir.text(response['new_path']);

                var file_list = "";
                $(response["list"]).each(function(i, f){
                    file_list += `<li class="col-md-6 list-group-item">
                                      <i class="mdi mdi-folder"></i>
                                      ${f}
                                  </li>`
                })
                file_list += `<li class="col-md-6 list-group-item">
                                  <i class="mdi mdi-folder"></i>
                                  ..
                              </li>`
                $modal_file_list.html(file_list);
            }
        })
        .fail(function(data){
            var err = data.status + ' ' + data.statusText
            $.notify({message: err}, {type: "danger", delay: 0});
        });
    });
});

function file_browser_select(event, elem){
    event.preventDefault();
    var $modal = $(elem).closest("div#modal_browser");

    var dir = $modal.find("div#modal_current_dir").text().trim();

    $dir_input.val(dir);

    $modal.modal("hide");
}

function scan_library(event, elem){
    event.preventDefault();

    directory = $dir_input.val();
    if(directory == ""){
        $dir_input.addClass("empty");
        return false;
    }

    var minsize = $("input#min_file_size").val()
    if(minsize == ""){
        $("input#min_size").addClass("empty");
        return false;
    } else {
        minsize = parseInt(minsize);
        if(minsize < 0){
            minsize = 0;
        }
    }

    var recursive = is_checked($("i#scan_recursive"))

    $("div#select_directory").slideUp();
    $("a#scan_dir").slideUp();
    $progress_bar.width("0%");
    $progress.slideDown();

    $complete_div = $("div#complete_movies");
    $complete_table = $("div#complete_movies table > tbody");
    $incomplete_div = $("div#incomplete_movies");
    $incomplete_table = $("div#incomplete_movies table > tbody");

    var no_imports = true;

    var last_response_len = false;
    $.ajax(url_base + '/ajax/scan_library_directory', {
        method: "POST",
        data: {"directory": directory, "minsize": minsize, "recursive": recursive},
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
                var response = JSON.parse(response_update);
                if(response['response'] == null){
                    return

                } else if(response["response"] == "incomplete"){
                    no_imports = false;
                    var movie = response["movie"];
                    var select = $(source_select);
                    select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);
                    var $row = $(`<tr>
                                    <td>
                                        <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                                    </td>
                                    <td>
                                        ${movie["finished_file"]}
                                    </td>
                                    <td>
                                        ${movie["title"]}
                                    </td>
                                    <td>
                                        <input type="text" class="incomplete_tmdbid form-control" placeholder="0000" value="${movie['tmdbid'] || ''}"/>
                                    </td>
                                    <td class="resolution">
                                        ${select[0].outerHTML}
                                    </td>
                                    <td>
                                        ${movie["human_size"]}
                                    </td>
                                </tr>`)
                    $row.data("movie", movie);
                    $row.find(`select.source_select > option[value="${movie['resolution']}"]`).attr("selected", true);
                    $incomplete_table.append($row);
                    $incomplete_div.show();

                } else if(response["response"] == "complete"){
                    no_imports = false;
                    var movie = response["movie"];
                    var select = $(source_select);
                    select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);
                    var $row = $(`<tr>
                                    <td>
                                        <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                                    </td>
                                    <td>
                                        ${movie["finished_file"]}
                                    </td>
                                    <td>
                                        ${movie["title"]}
                                    </td>
                                    <td>
                                        ${movie["tmdbid"]}
                                    </td>
                                    <td class="resolution">
                                        ${select[0].outerHTML}
                                    </td>
                                    <td>
                                        ${movie["human_size"]}
                                    </td>
                                </tr>`)
                    $row.data("movie", movie);
                    $row.find(`select.source_select > option[value="${movie['resolution']}"]`).attr("selected", true);
                    $complete_table.append($row);
                    $complete_div.show();
                }

                var progress_text = `${response['progress'][0]} / ${response['progress'][1]} ${response['movie']['title']} ${response['response']}.`.replace("_", " ");
                var progress_percent = Math.round(parseInt(response['progress'][0]) / parseInt(response['progress'][1]) * 100);

                $progress_text.text(progress_text);
                $progress_bar.width(progress_percent + "%")
            }
        }
    })
    .done(function(data){
        window.setTimeout(function(){
            $progress.slideUp();
            $progress_text.slideUp();
            if(no_imports == false){
                $("a#import_library").slideDown();
            } else {
                $("div#no_new_movies").slideDown();
                $("a#import_return").slideDown();
            }
        }, 500)
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
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
        movie["tmdbid"] = $row.find("input.incomplete_tmdbid").val();

        if(!movie["tmdbid"]){
            blanks = true;
            $row.find("input.incomplete_imdbid").addClass("empty");
            return
        }

        movie["resolution"] = $row.find("select.source_select").val();
        corrected_movies.push(movie);
    });

    if(blanks){
        $.notify({message: _("Fill highlighted fields or disable movie to continue.")}, {type: "warning"});
        return false;
    }

    $("div#complete_movies").slideUp();
    $("div#incomplete_movies").slideUp();
    $("a#import_library").slideUp();
    $progress_bar.width("0%");
    $progress.slideDown();

    var $success = $("div#import_success");
    var $success_table = $("div#import_success table > tbody");
    var $error = $("div#import_error");
    var $error_table = $("div#import_error table > tbody")
    $progress_text.text("").show();

    var last_response_len = false;
    $.ajax(url_base + '/ajax/import_dir', {
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

                var progress_text = `${r['progress'][0]} / ${r['progress'][1]} ${r['movie']['title']}.`;
                var progress_percent = Math.round(parseInt(r['progress'][0]) / parseInt(r['progress'][1]) * 100);

                $progress_text.text(progress_text);

                $progress_bar.width(progress_percent + "%")
                if(r['response'] == true){
                    $success.slideDown()
                    var row = `<tr>
                                    <td>${r['movie']['title']}</td>
                                    <td>${r['movie']['tmdbid']}</td>
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

