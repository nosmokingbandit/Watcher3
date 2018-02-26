function connect(event, elem){
    event.preventDefault();

    var $address_input = document.getElementById('address');
    if(!$address_input.value){
        $address_input.classList.add('border-danger');
        return false
    }

    var parts = $address_input.value.split("//");
    if(parts.length > 1){
        var [scheme, address] = parts;
    }

    var $port_input = document.getElementById('port');
    if(!$port_input){
        $port_input.classList.add('border-danger');
        return false
    }

    var user = document.getElementById('user').value;
    var password = document.getElementById('password').value;

    var url = "";

    if(scheme){
        url += scheme + "//";
    } else {
        url += "http://"
    }

    if(user && password){
        url += `${user}:${password}@`
    }

    url += `${$address_input.value}:${$port_input.value}`

    $("form#connect").slideUp();
    $progress_bar.style.width = '0%';
    $progress.style.maxHeight = '100%';

    $complete_div = document.querySelector("div#complete_movies");
    $complete_table = document.querySelector("div#complete_movies table > tbody");
    $incomplete_div = document.querySelector("div#incomplete_movies");
    $incomplete_table = document.querySelector("div#incomplete_movies table > tbody");

    $.post(url_base+"/ajax/get_kodi_movies", {
        "url": url
    })
    .done(function(response){
        if(response["response"] !== true){
            $("form#connect").slideDown();
            $.notify({message: response["error"]}, {type: "warning"})
            return false
        }

        if(response["movies"].length == 0){
            document.getElementById('no_imports').classList.remove('hidden');
        } else {
            document.getElementById('remote_map').classList.remove('hidden');
        }



        var $scanned_div = $("div#scanned_movies");
        var $scanned_table = $("div#scanned_movies table tbody");

        each(response['movies'], function(movie, index){
            var select = $source_select.cloneNode(true);
            select.querySelector(`option[value="${movie["resolution"]}"]`).setAttribute("selected", true);
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
                                ${movie["imdbid"]}
                            </td>
                            <td class="resolution">
                                ${select.outerHTML}
                            </td>
                        </tr>`)[0]
            $row.dataset.movie = JSON.stringify(movie);
            $complete_table.innerHTML += $row.outerHTML;
            $complete_div.classList.remove('hidden');
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

    var movies = [];

    each(document.querySelectorAll("div#complete_movies table > tbody > tr "), function(row, index){
        if(!is_checked(row.querySelector('i.c_box'))){
            return
        }

        movie = JSON.parse(row.dataset.movie);
        movie["finished_file"] = row.querySelector("td.file_path").innerText.trim();
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
    $.ajax(url_base + '/ajax/import_kodi_movies', {
        method: "POST",
        data: {"movies": JSON.stringify(movies)},
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
        $.notify({message: err}, {type: "danger", delay: 0});
    })
}

