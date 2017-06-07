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
        .done(function(r){
            response = JSON.parse(r);

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
        });
    });

});

function file_browser_select(event, elem){
    event.preventDefault();
    var $modal = $(elem).closest("div#modal_browser");

    var dir = $modal.find("div#modal_current_dir").text().replace(/ /g,'');;

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

    var no_imports = false;

    var last_response_len = false;
    $.ajax(url_base + '/ajax/scan_library_directory', {
        method: "POST",
        data: {"directory": directory, "minsize": minsize, "recursive": recursive},
        xhrFields: {
            onprogress: function(e)
            {
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
                    $("div#no_new_movies").slideDown();
                    $("a#import_return").slideDown();
                    no_imports = true;

                } else if(response["response"] == "incomplete"){
                    var movie = response["movie"];
                    var select = $(source_select);
                    select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);
                    var $row = $(`<tr>
                                    <td>
                                        <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                                    </td>
                                    <td>
                                        ${movie["path"]}
                                    </td>
                                    <td>
                                        ${movie["title"]}
                                    </td>
                                    <td>
                                        <input type="text" class="incomplete_imdbid" placeholder="tt0123456" value="${movie['imdbid']}"/>
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
                    var movie = response["movie"];
                    var select = $(source_select);
                    select.children(`option[value="${movie["resolution"]}"]`).attr("selected", true);
                    var $row = $(`<tr>
                                    <td>
                                        <i class="mdi mdi-checkbox-marked c_box", value="True"></i>
                                    </td>
                                    <td>
                                        ${movie["path"]}
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
                                    <td>
                                        ${movie["human_size"]}
                                    </td>
                                </tr>`)
                    $row.data("movie", movie);
                    $row.find(`select.source_select > option[value="${movie['resolution']}"]`).attr("selected", true);
                    $complete_table.append($row);
                    $complete_div.show();
                }

                var progress_text = `${response['progress'][0]} / ${response['progress'][1]}`;
                var progress_percent = Math.round(parseInt(response['progress'][0]) / parseInt(response['progress'][1]) * 100);

                $progress_text.text(`${response['progress'][0]} / ${response['progress'][1]}`);
                $progress_bar.width(progress_percent + "%")
            }
        }
    })
    .done(function(data){
        $progress.slideUp();
        $progress_text.empty();
        if(no_imports == false){
            $("a#import_library").slideDown();
        }

    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    });
};

function import_library(event, elem){
    event.preventDefault();

    $("div#complete_movies").slideUp();
    $("div#incomplete_movies").slideUp();
    $("a#import_library").slideUp();
    $progress_bar.width("0%");
    $progress.slideDown();

    var movies = [];
    var corrected_movies = [];

    $("div#complete_movies table > tbody > tr ").each(function(i, row){
        var $row = $(row);
        if(!is_checked($row.find("i.c_box"))){
            return
        }

        movie = $row.data("movie");
        movie["finished_file"] = $row.find("td.file_path").text();
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

        movie["finished_file"] = $row.find("td.file_path").text();
        movie["resolution"] = $row.find("select.source_select").val();
        corrected_movies.push(movie);
    });

    if(blanks){
        $.notify({message: "Please fill highlighted fields or disable movie to continue."}, {type: "warning"});
        return false;
    }

    var $success = $("div#import_success");
    var $success_table = $("div#import_success table > tbody");
    var $error = $("div#import_error");
    var $error_table = $("div#import_error table > tbody")

    var last_response_len = false;
    $.ajax(url_base + '/ajax/import_dir', {
        method: "POST",
        data: {"movies": JSON.stringify(movies),
               "corrected_movies": JSON.stringify(corrected_movies)
               },
        xhrFields: {
            onprogress: function(e)
            {
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

                var progress_text = `${r['progress'][0]} / ${r['progress'][1]}`;
                var progress_percent = Math.round(parseInt(r['progress'][0]) / parseInt(r['progress'][1]) * 100);

                $progress_text.text(`${r['progress'][0]} / ${r['progress'][1]}`);

                $progress_bar.width(progress_percent + "%")
                if(r['response'] == true){
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
        $progress_bar.width("0%");
        $progress_text.empty();
        $('a#import_return').slideDown();
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    });
}
