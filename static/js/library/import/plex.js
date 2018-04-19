var import_cache;

var template_import_complete = (index, movie, select) => $(`<tr data-index="${index}">
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
                                                                    ${select}
                                                                </td>
                                                            </tr>`)[0]

var template_import_incomplete = (index, movie, select) => $(`<tr data-index="${index}">
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
                                                                    ${select}
                                                                </td>
                                                            </tr>`)[0]

function connect(event, elem){
    event.preventDefault();

    var file_input = document.getElementById('csv_file');
    if(file_input.files.length == 0){
        $.notify({message: 'Select a CSV'}, {type: 'warning'})
        return false
    }

    var post_data = new FormData();
    post_data.append('file_input', file_input.files[0])

    $("form#connect").slideUp();
    $progress_bar.style.width = '0%';
    $progress.style.maxHeight = '100%';

    $complete_div = document.querySelector("div#complete_movies");
    $complete_table = document.querySelector("div#complete_movies table > tbody");
    $incomplete_div = document.querySelector("div#incomplete_movies");
    $incomplete_table = document.querySelector("div#incomplete_movies table > tbody");

    $.ajax({
        url: url_base+'/ajax/upload_plex_csv',
        type: 'POST',
        data: post_data,
        processData: false,
        contentType: false
    })
    .done(function(response){
        if(response["response"] !== true){
            $("form#connect").slideDown();
            $.notify({message: response["error"]}, {type: "warning"})
            return false
        }


        if(response["complete"].length + response["incomplete"].length == 0){
            document.getElementById('no_imports').classList.remove('hidden');
        }

        import_cache = response;

        if(response['complete'].length > 0){
            $complete_div.classList.remove('hidden');
        };
        each(response['complete'], function(movie, index){
            if(movie['imdbid']){
                id = movie['imdbid']
            } else {
                id = movie['tmdbid']
            }

            var select = $source_select.cloneNode(true);
            select.querySelector(`option[value="${movie["resolution"]}"]`).setAttribute("selected", true);

            var row = template_import_complete(index, movie, select.outerHTML);
            $complete_table.innerHTML += row.outerHTML;
        });

        if(response['incomplete'].length > 0){
            $incomplete_div.classList.remove('hidden');
        };
        each(response['incomplete'], function(movie, index){
            var select = $source_select.cloneNode(true);
            select.querySelector(`option[value="${movie["resolution"]}"]`).setAttribute("selected", true);

            var row = template_import_incomplete(index, movie, select.outerHTML);
            $incomplete_table.innerHTML += row.outerHTML;
        });

        set_stepper('import');
        document.getElementById('button_import').classList.remove('hidden');

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
}

function apply_remote(event){
    event.preventDefault();
    var local = document.getElementById("local_path").value;
    var remote = document.getElementById("remote_path").value;
    each(document.querySelectorAll("div#complete_movies table > tbody > tr td.file_path"), function(row, index){
        row.innerText = row.innerText.replace(remote, local);
    })
    each(document.querySelectorAll("div#incomplete_movies table > tbody > tr td.file_path"), function(row, index){
        row.innerText = row.innerText.replace(remote, local);
    })
};

function reset_remote(event){
    event.preventDefault();
    each(document.querySelectorAll("div#complete_movies table > tbody > tr td.file_path"), function(row, index){
        row.innerText = row.dataset.original;
    })
    each(document.querySelectorAll("div#incomplete_movies table > tbody > tr td.file_path"), function(row, index){
        row.innerText = row.dataset.original;
    })
};

function start_import(event, elem){
    event.preventDefault();

    var corrected_movies = [];
    var blanks = false;
    each(document.querySelectorAll("div#incomplete_movies table > tbody > tr "), function(row, index){
        if(!is_checked(row.querySelector('i.c_box'))){
            return
        }

        movie = import_cache['incomplete'][row.dataset.index];
        var $tmdbid_input = row.querySelector("input.incomplete_imdbid");

        movie["imdbid"] = $tmdbid_input.value;

        if(!movie["imdbid"]){
            blanks = true;
            $tmdbid_input.classList.add("border-danger");
            return
        }

        movie["finished_file"] = movie['file'].trim();
        movie["resolution"] = row.querySelector("select.source_select").value;
        corrected_movies.push(movie);
    });

    var movies = [];
    each(document.querySelectorAll("div#complete_movies table > tbody > tr "), function(row, index){
        if(!is_checked(row.querySelector('i.c_box'))){
            return
        }

        movie = import_cache['complete'][row.dataset.index];

        movie["finished_file"] = movie['file'].trim();
        movie["resolution"] = row.querySelector("select.source_select").value;
        movies.push(movie);
    });

    if(blanks){
        $.notify({message: _("Fill highlighted fields or disable movie to continue.")}, {type: "warning"});
        return false;
    }

    $('form#import').slideUp(600);
    $progress_bar.style.width = '0%';
    $progress.style.maxHeight = '100%';

    var $success_div = document.querySelector("div#import_success");
    var $success_table = document.querySelector("div#import_success table > tbody");
    var $error_div = document.querySelector("div#import_error");
    var $error_table = document.querySelector("div#import_error table > tbody");

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

                if(r['response'] == true){
                    $success_div.classList.remove('hidden');
                    var row = `<tr>
                                    <td>${r['title']}</td>
                                    <td>${r['imdbid']}</td>
                                </tr>`
                    $success_table.innerHTML += row;
                } else {
                    $error_div.classList.remove('hidden');
                    var row = `<tr>
                                    <td>${r['title']}</td>
                                    <td>${r['error']}</td>
                                </tr>`
                    $error_table.innerHTML += row;
                }

                var progress_percent = Math.round(parseInt(r['progress'][0]) / parseInt(r['progress'][1]) * 100);
                $progress_text.innerText = `${r['progress'][0]} / ${r['progress'][1]} ${r['title']}`;
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

