window.addEventListener("DOMContentLoaded", function(){
    $dir_input = document.getElementById("directory_input");

    $modal_current_dir = document.querySelector("input#modal_current_dir");
    $modal_file_list = $("ul#modal_file_list");

    $modal_file_list.on("click", "li", function(){
        $this = $(this);
        $.post(url_base+'/ajax/list_files', {
            "current_dir": $modal_current_dir.value,
            "move_dir": $this.text().trim()
        })
        .done(function(response){
            if(response['error']){
                $.notify({message: response['error']}, {type: "danger"})
            } else {
                $modal_current_dir.value = response['new_path'];

                var file_list = "";
                $(response["list"]).each(function(i, f){
                    file_list += `<li class="col-md-6 p-1 border">
                                      <i class="mdi mdi-folder"></i>
                                      ${f}
                                  </li>`
                })
                file_list += `<li class="col-md-6 p-1 border">
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
    var dir = $modal_current_dir.value.trim();
    $dir_input.value = dir;
    //$modal.modal("hide");
}

function connect(event, elem){
    event.preventDefault();

    directory = $dir_input.value;
    if(directory == ""){
        $dir_input.classList.add("border-danger");
        return false;
    }

    var $minsize = document.getElementById("min_file_size");
    var minsize = $minsize.value;
    if(minsize == ""){
        $minsize.classList.add("border-danger");
        return false;
    } else {
        minsize = parseInt(minsize);
        if(minsize < 0){
            minsize = 0;
        }
    };

    var recursive = is_checked(document.getElementById("scan_recursive"))

    $('form#connect').slideUp(600);
    $progress_bar.style.width = '0%';
    $progress.style.maxHeight = '100%';

    $complete_div = document.querySelector("div#complete_movies");
    $complete_table = document.querySelector("div#complete_movies table > tbody");
    $incomplete_div = document.querySelector("div#incomplete_movies");
    $incomplete_table = document.querySelector("div#incomplete_movies table > tbody");

    no_imports = true;
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
                }

                if(response['response'] != 'in_library'){
                    var movie = response["movie"];
                    var select = $source_select.cloneNode(true);
                    select.querySelector(`option[value="${movie["resolution"]}"]`).setAttribute("selected", true);
                }

                if(response["response"] == "incomplete"){
                    no_imports = false;
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
                                        <input type="number" class="incomplete_tmdbid form-control form-control-sm" placeholder="0000" value="${movie['tmdbid'] || ''}"/>
                                    </td>
                                    <td class="resolution">
                                        ${select.outerHTML}
                                    </td>
                                    <td>
                                        ${movie["human_size"]}
                                    </td>
                                </tr>`)[0]
                    $row.dataset.movie = JSON.stringify(movie);
                    $incomplete_table.innerHTML += $row.outerHTML;
                    $incomplete_div.classList.remove('hidden');
                } else if(response["response"] == "complete"){
                    no_imports = false;
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
                                        ${select.outerHTML}
                                    </td>
                                    <td>
                                        ${movie["human_size"]}
                                    </td>
                                </tr>`)[0]
                    $row.dataset.movie = JSON.stringify(movie);
                    $complete_table.innerHTML += $row.outerHTML;
                    $complete_div.classList.remove('hidden');
                }

                var progress_percent = Math.round(parseInt(response['progress'][0]) / parseInt(response['progress'][1]) * 100);
                $progress_text.innerText = `${response['progress'][0]} / ${response['progress'][1]} ${response['movie']['title']}.`.replace("_", " ");
                $progress_bar.style.width = (progress_percent + "%");
            }
        }
    })
    .done(function(data){
        set_stepper('import');

        if(no_imports == true){
            document.getElementById('no_imports').classList.remove('hidden');
        } else {
            document.getElementById('button_import').classList.remove('hidden');
        }

        $("form#import").slideDown();
        window.setTimeout(function(){
            $progress.style.maxHeight = '0%';
            $progress_text.innerText = '';
            $progress_bar.style.width = '0%';
        }, 500)
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });
};

function start_import(event, button){
    event.preventDefault();

    var corrected_movies = [];
    var blanks = false;
    each(document.querySelectorAll("div#incomplete_movies table > tbody > tr "), function(row, index){
        if(!is_checked(row.querySelector('i.c_box'))){
            return
        }

        movie = JSON.parse(row.dataset.movie);

        var $tmdbid_input = row.querySelector("input.incomplete_tmdbid")
        movie["tmdbid"] = $tmdbid_input.value;

        if(!movie["tmdbid"]){
            blanks = true;
            $tmdbid_input.classList.add("border-danger");
            return
        }

        movie["resolution"] = row.querySelector("select.source_select").value;
        corrected_movies.push(movie);
    });

    if(blanks){
        $.notify({message: _("Fill highlighted fields or disable movie to continue.")}, {type: "warning"});
        return false;
    }

    var movies = [];
    each(document.querySelectorAll("div#complete_movies table > tbody > tr "), function(row, index){
        if(!is_checked(row.querySelector('i.c_box'))){
            return
        }

        movie = JSON.parse(row.dataset.movie);
        movie["resolution"] = row.querySelector("select.source_select").value;
        movies.push(movie);
    });

    $('form#import').slideUp(600);
    $progress_bar.style.width = '0%';
    $progress.style.maxHeight = '100%';

    var $success_div = document.querySelector("div#import_success");
    var $success_table = document.querySelector("div#import_success table > tbody");
    var $error_div = document.querySelector("div#import_error");
    var $error_table = document.querySelector("div#import_error table > tbody");

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

                if(r['response'] == true){
                    $success_div.classList.remove('hidden');
                    var row = `<tr>
                                    <td>${r['movie']['title']}</td>
                                    <td>${r['movie']['tmdbid']}</td>
                                </tr>`
                    $success_table.innerHTML += row;
                } else {
                    $error_div.classList.remove('hidden');
                    var row = `<tr>
                                    <td>${r['movie']['title']}</td>
                                    <td>${r['error']}</td>
                                </tr>`
                    $error_table.innerHTML += row;
                }

                var progress_percent = Math.round(parseInt(r['progress'][0]) / parseInt(r['progress'][1]) * 100);
                $progress_text.innerText = `${r['progress'][0]} / ${r['progress'][1]} ${r['movie']['title']}.`;
                $progress_bar.style.width = (progress_percent + "%");

            }
        }
    })
    .done(function(data){
        set_stepper('review');
        $("form#review").slideDown();
        window.setTimeout(function(){
            $progress.style.maxHeight = '0%';
            $progress_text.innerText = '';
            $progress_bar.style.width = '0%';
        }, 500)
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger"});
    })
}

