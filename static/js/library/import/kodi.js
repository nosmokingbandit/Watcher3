function scan_library(event, elem){
    event.preventDefault();

    var address = $("input#address").val();
    if(!address){
        $("input#address").addClass("empty");
        return false
    }

    var parts = address.split("//");
    if(parts.length > 1){
        var [scheme, address] = parts;
    }

    var port = $("input#port").val();
    if(!port){
        $("input#port").addClass("empty");
        return false
    }

    var user = $("input#user").val();
    var password = $("input#password").val();

    var url = "";

    if(scheme){
        url += scheme + "//";
    } else {
        url += "http://"
    }

    if(user && password){
        url += `${user}:${password}@`
    }

    url += `${address}:${port}`


    $("div#server_info").slideUp();
    $("a#scan_library").slideUp();
    $progress.slideDown();

    $.post(url_base+"/ajax/get_kodi_movies", {
        "url": url
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

        $("div#remote_map").slideDown();

        var $scanned_div = $("div#scanned_movies");
        var $scanned_table = $("div#scanned_movies table tbody");

        $.each(response["movies"], function(index, movie){
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
                                ${movie["imdbid"]}
                            </td>
                            <td class="resolution">
                                ${select[0].outerHTML}
                            </td>
                        </tr>`)
            $row.data("movie", movie);
            $row.find(`select.source_select > option[value="${movie['resolution']}"]`).attr("selected", true);
            $scanned_table.append($row);
            $scanned_div.show();
        });
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
    $("div#scanned_movies table > tbody > tr td.file_path").each(function(i, elem){
        $elem = $(elem);
        $elem.text($elem.text().replace(remote, local));
    })
};

function reset_remote(event){
    event.preventDefault();
    $("div#scanned_movies table > tbody > tr td.file_path").each(function(i, elem){
        var $elem = $(elem);
        $elem.text($elem.data("original"));
    })
};

function import_library(event, elem){
    event.preventDefault();

    var kodi_movies = [];

    $("div#remote_map").slideUp();
    $("div#scanned_movies").slideUp();
    $("a#import_library").slideUp();
    $progress_bar.width("0%");
    $progress.slideDown();

    $("div#scanned_movies table > tbody > tr ").each(function(i, row){
        var $row = $(row);
        if(!is_checked($row.find("i.c_box"))){
            return
        }

        movie = $row.data("movie");
        movie["finished_file"] = $row.find("td.file_path").text().trim();
        movie["resolution"] = $row.find("select.source_select").val();
        kodi_movies.push(movie);
    });

    var $success = $("div#import_success");
    var $success_table = $("div#import_success table > tbody");
    var $error = $("div#import_error");
    var $error_table = $("div#import_error table > tbody")

    var last_response_len = false;
    $.ajax(url_base + '/ajax/import_kodi_movies', {
        method: "POST",
        data: {"movies": JSON.stringify(kodi_movies)},
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

                var progress_text = `${r['progress'][0]} / ${r['progress'][1]} ${r['movie']['title']} ${r['movie']['title']}.`;
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
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $('a#import_return').slideDown();
    });
}

