$(document).ready(function() {
    var url_base = $("meta[name='url_base']").attr("content");
    var directory = "";
    var resolutions = JSON.parse($('#resolution_list').text());
    resolution_select = $("<select class='input_resolution'></select>");
    $.each(resolutions, function(i, v){
        resolution_select.append(`<option value=${v}>${v}</option>`)
    })

    var $content = $("div#content");

// Import directory

    // file browser
    $file_list = $("ul#file_list");

    $current_dir = $("div#current_dir")

    $("div#browse").click(function(){
        $("div#browser").show();
        $("div#overlay").fadeIn();
    });

    $("i#close_browser").click(function(){
        $("div#browser").hide();
        $("div#overlay").fadeOut();
    });

    $("i#select_dir").click(function(){
        $("input#directory").val($current_dir.text());
        $("div#browser").hide();
        $("div#overlay").fadeOut();
    });

    $file_list.on("click", "li", function(){
        $this = $(this)
        var path = $this.text()
        $.post(url_base+'/ajax/list_files', {"current_dir": $current_dir.text(),
                                          "move_dir": path})
        .done(function(r){
            response = JSON.parse(r);

            if(response['error']){
                toastr.warning(response['error'])
            } else {
                $current_dir.text(response['new_path'])
                $file_list.html(response['html']);
            }
        });
    });

    // submit directory information
    $("span#start_scan").click(function(e){
        directory = $("input#directory").val();
        if(directory == ""){
            highlight($("input#directory"));
            return false;
        }

        var minsize = $("input#minsize").val()
        if(minsize == ""){
            highlight($("input#minsize"));
            return false;
        } else {
            minsize = parseInt(minsize);
        }

        var recursive = is_checked($("i#recursive"))

        $("div#directory_info").hide();
        $("div#wait_scanning").fadeIn();
        $("div#list_files").fadeIn();

        e.preventDefault();
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
                    var movie = JSON.parse(response_update);
                    render_movie(movie)
                }
            }
        })
        .done(function(data)
        {
            $("div#wait_scanning").slideUp();
            if($('div#scan_success table').length == 1 && $('div#scan_missing table').length == 1){
                $('div#no_new_movies').slideDown();
                $('span#import').slideUp();
                return
            } else {
                $('span#import').slideDown();
            }
        })
        .fail(function(data)
        {
            var err = data.status + ' ' + data.statusText
            toastr.error(err);
        });
    });

    function render_movie(response){
        // Renders movie output from importer
        // response: response from ajax handler
        // Appends html to appropriate table in DOM

        var $scan_progress_bar = $('span#scan_progress span.progress_bar');
        var progress_percent = (response['progress'][0] / response['progress'][1]) * 100 + '%';
        var $scan_progress_text = $('span#scan_progress_text');
        var progress_text = `${response['progress'][0]} / ${response['progress'][1]}`

        var movie = response['movie']

        if(response['response'] == 'in_library'){
            $scan_progress.width(progress_percent);
            $scan_progress_text.text(progress_text);
            return
        } else if(response['response'] == 'complete'){
            $('div#scan_success').show()
            $scan_progress_bar.width(progress_percent);
            $scan_progress_text.text(progress_text);
            var short_path = movie['path'].replace(directory, '')
            var select = resolution_select;
            select.children(`option`).removeAttr('selected')
            select.children(`option[value="${movie['resolution']}"]`).attr('selected', 'selected');
            row = `
                <tr>
                    <td>
                        <i class='fa fa-check-square checkbox', value='True'/>
                        <span class='hidden data'>${JSON.stringify(movie)}</span>
                    </td>
                    <td cls='short_name'>
                        ${short_path}
                    </td>
                    <td>
                        ${movie['title']}
                    </td>
                    <td>
                        ${movie['imdbid']}
                    </td>
                    <td>
                        ${select[0].outerHTML}

                    </td>
                    <td>
                        ${movie['human_size']}
                    </td>
            `
            $('div#scan_success table').append(row);
            return
        }
        else if(response['response'] == 'incomplete'){
            $('div#scan_missing').show();
            $scan_progress_bar.width(progress_percent);
            $scan_progress_text.text(progress_text);
            var size = movie['size']
            var short_path = movie['path'].replace(directory, '')
            var select = resolution_select;
            var imdbid = movie['imdbid'] || '';
            select.children(`option`).removeAttr('selected');
            select.children(`option[value="${movie['resolution']}"]`).attr('selected', 'selected');
            row = `
                <tr>
                    <td>
                        <i class='fa fa-check-square checkbox', value='True'/>
                        <span class='hidden data'>${JSON.stringify(movie)}</span>
                    </td>
                    <td cls='short_name'>
                        ${short_path}
                    </td>
                    <td>
                        ${movie['title']}
                    </td>
                    <td>
                        <input type='text' class='input_imdbid', placeholder='tt0123456' value=${imdbid}></input>
                    </td>
                    <td>
                        ${select[0].outerHTML}

                    </td>
                    <td>
                        ${movie['human_size']}
                    </td>
            `
            $('div#scan_missing table').append(row);
            return
        }
    }

    // Send import instructions
    $content.on("click", "span#import", function(){
        movie_data = [];
        corrected_movies = [];

        corrected_movies = _get_corrected_movies();
        movie_data = _get_movie_data();

        if(movie_data.length == 0 && corrected_movies.length == 0){
            toastr.warning("All imports disabled.");
            return false
        } else {

            if(corrected_movies === false){
                return false
            }

            movie_data = JSON.stringify(movie_data)
            corrected_movies = JSON.stringify(corrected_movies);

            _submit_import(movie_data, corrected_movies)
        }
    });

    function _get_movie_data(){
        movie_data = [];
        var $rows = $("div#scan_success table tr")
        $.each($rows, function(){
            $this = $(this);
            if(is_checked($this.find("i"))){
                metadata = JSON.parse($this.find('span.data').text());
                metadata['resolution'] = $this.find("select.input_resolution").val();
                metadata['filepath'] = directory + $.trim($this.find("td.short_name").text());
                movie_data.push(metadata);
            }
        })
        return movie_data || [];
    }

    function _get_corrected_movies(){
        corrected_movies = []
        var $rows = $("div#scan_missing table tr")
        var cancel = false;

        $.each($rows, function(idx, elem){
            $elem = $(elem);
            if(is_checked($elem.find("i"))){
                var imdbid = $elem.find("input.input_imdbid").val();
                var resolution = $elem.find("select.input_resolution").val();
                var metadata = JSON.parse($elem.find('span.data').text());

                if($.trim(imdbid) == ''){
                    cancel = true;
                    highlight($elem.find("input.input_imdbid"))
                    return false;
                }
                metadata['imdbid'] = imdbid;
                metadata['resolution'] = resolution;
                metadata['filepath'] = directory + $.trim($elem.find("td.short_name").text());
                corrected_movies.push(metadata);
            }
        })
        if(cancel){
            return false
        } else {
            return corrected_movies;
        }
    }

    function _submit_import(movie_data, corrected_movies){
        $("div#list_files").hide();
        $('div#wait_importing').fadeIn();
        $('div#import_results').fadeIn();

        var $import_progress_text = $('div#wait_importing span#import_progress_text');
        var $import_progress_bar = $('span#import_progress span.progress_bar');
        var $success_table = $('table#import_success')
        var $error_table = $('table#import_error')
        var last_response_len = false;
        $.ajax(url_base + '/ajax/import_dir', {
            method: "POST",
            data: {"movie_data": movie_data, "corrected_movies": corrected_movies},
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
                    var progress_percent = (r['progress'][0] / r['progress'][1]) * 100 + '%';
                    $import_progress_text.text(progress_text)
                    $import_progress_bar.width(progress_percent)
                    if(r['response'] === true){
                        $success_table.show()
                        var row = `<tr>
                                       <td>${r['movie']['title']}</td>
                                       <td>${r['movie']['imdbid']}</td>
                                   </tr>`
                        $success_table.append(row)
                    } else {
                        $error_table.show()
                        var row = `<tr>
                                       <td>${r['movie']['title']}</td>
                                       <td>${r['error']}</td>
                                   </tr>`
                        $error_table.append(row)
                    }
                }
            }
        })
        .done(function(data)
        {
            $("div#wait_importing").slideUp();
            $('a#finished').slideDown();
        })
        .fail(function(data)
        {
            var err = data.status + ' ' + data.statusText
            toastr.error(err);
        });
    }

// Kodi Import
    $("div#start_import_kodi").click(function(){
        var scheme = $('select#scheme').val();
        var address = $('input#kodi_address').val();
        if(!address){
            highlight($('input#kodi_address'));
            return false
        }

        var port = $('input#kodi_port').val();
        if(!port){
            highlight($('input#kodi_port'));
            return false
        }

        var user = $('input#kodi_user').val();
        var password = $('input#kodi_pass').val();

        if(user && password){
            var url = `${scheme}${user}:${password}@${address}:${port}`
        } else {
            var url = `${scheme}${address}:${port}`
        }

        $('div#kodi_server_info').slideUp();
        $('div#thinker').fadeIn();

        $.post(url_base + '/ajax/get_kodi_movies/', {'url': url})
        .done(function(r){
            response = JSON.parse(r);

            if(!response['response']){
                toastr.error(response['error'])
                $('div#thinker').fadeOut();
                $('div#kodi_server_info').slideDown();
                return false
            }

            var movies = response['movies']
            if(movies.length == 0){
                $('div#no_new_movies').slideDown();
                $('div#thinker').fadeOut();
                return false
            }
            var $table = $('div#kodi_response table')
            $.each(movies, function(index, movie){
                var select = resolution_select;
                select.children(`option`).removeAttr('selected')
                select.children(`option[value="${movie['resolution']}"]`).attr('selected', 'selected');
                row = `<tr>
                            <td>
                                <i class='fa fa-check-square checkbox', value='True'/>
                                <span class='hidden data'>${JSON.stringify(movie)}</span>
                            </td>
                            <td class='file_location' data-original="${movie['file']}">
                                ${movie['file']}
                            </td>
                            <td>
                                ${movie['title']}
                            </td>
                            <td>
                                ${movie['imdbid']}
                            </td>
                            <td class='resolution'>
                                ${select[0].outerHTML}
                            </td>
                      `
                $table.append(row)
            });

            $('div#thinker').fadeOut();
            $('div#kodi_response').slideDown();
            $('span#kodi_import').slideDown();

        });
    })

    $("button#kodi_apply_remote").click(function(){
        var local = $('input#kodi_local_path').val()
        var remote = $('input#kodi_remote_path').val()

        $('div#kodi_response table td.file_location').each(function(index, elem){
            var $elem = $(elem);
            var new_path = $elem.text().replace(remote, local)
            $elem.text(new_path);
        })
    })

    $("button#kodi_reset_remote").click(function(){
        $('div#kodi_response table td.file_location').each(function(index, elem){
            var $elem = $(elem);
            $elem.text($elem.attr('data-original'));
        })
    })

    $('span#kodi_import').click(function(){
        var movies = [];
        $('div#kodi_response table tr').each(function(index, elem){
            var $row = $(elem);
            if(!is_checked($row.find('i.checkbox'))){
                return 'continue'
            }

            movie = JSON.parse($row.find('span.data').text())
            movie['finished_file'] = $row.find('td.file_location').text().trim()
            movie['resolution'] = $row.find('td.resolution select').val();
            movies.push(movie);
        })

        $('div#kodi_response').slideUp();
        $('div#kodi_import_results').slideDown();
        $('div#kodi_wait_importing').slideDown();

        var $import_progress_text = $('div#kodi_wait_importing span#import_progress_text');
        var $import_progress_bar = $('div#kodi_wait_importing span.progress_bar');
        var $success_table = $('table#kodi_import_success')
        var $error_table = $('table#kodi_import_error')
        var last_response_len = false;
        $.ajax(url_base + '/ajax/import_kodi', {
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
                    var progress_text = `${r['progress'][0]} / ${r['progress'][1]}`;
                    var progress_percent = (r['progress'][0] / r['progress'][1]) * 100 + '%';
                    $import_progress_text.text(progress_text)
                    $import_progress_bar.width(progress_percent)
                    if(r['response'] === true){
                        $success_table.show()
                        var row = `<tr>
                                       <td>${r['movie']['title']}</td>
                                       <td>${r['movie']['imdbid']}</td>
                                   </tr>`
                        $success_table.append(row)
                    } else {
                        $error_table.show()
                        var row = `<tr>
                                       <td>${r['movie']['title']}</td>
                                       <td>${r['error']}</td>
                                   </tr>`
                        $error_table.append(row)
                    }
                }
            }
        })
        .done(function(data)
        {
            $("div#kodi_wait_importing").slideUp();
            $('a#finished').slideDown();
        })
        .fail(function(data)
        {
            var err = data.status + ' ' + data.statusText
            toastr.error(err);
        });

    });

// Plex Import
    $('div#start_import_plex').click(function(){
        var file_input = document.getElementById('plex_csv');
        if(file_input.files.length == 0){
            highlight($('input#plex_csv'));
            return false
        }

        post_data = new FormData();
        post_data.append('file_input', file_input.files[0])

        $('div#plex_csv_form').slideUp();
        $('div#thinker').fadeIn();

        $.ajax({
            url: url_base+'/ajax/upload_plex_csv',
            type: 'POST',
            data: post_data,
            processData: false,
            contentType: false
        }).done(function(r){
            response = JSON.parse(r);

            if(!response['response']){
                toastr.error(response['error'])
                $('div#thinker').fadeOut();
                $('div#plex_csv_form').slideDown();
                return false
            }

            var movies = response['movies']
            var incomplete = response['incomplete']
            if(movies.length == 0 && incomplete.length == 0){
                $('div#no_new_movies').slideDown();
                $('div#thinker').fadeOut();
                return false
            }
            var $table = $('div#plex_parsed_csv table#complete');
            $.each(movies, function(index, movie){
                var select = resolution_select;
                select.children(`option`).removeAttr('selected')
                select.children(`option[value="${movie['resolution']}"]`).attr('selected', 'selected');
                console.log(movie)
                if(movie['imdbid']){
                    id = movie['imdbid']
                } else if(movie['tmdbid']) {
                    id = movie['tmdbid']
                }

                row = `<tr>
                            <td>
                                <i class='fa fa-check-square checkbox', value='True'/>
                                <span class='hidden data'>${JSON.stringify(movie)}</span>
                            </td>
                            <td class='file_location' data-original="${movie['file']}">
                                ${movie['file']}
                            </td>
                            <td>
                                ${movie['title']}
                            </td>
                            <td>
                                ${id}
                            </td>
                            <td class='resolution'>
                                ${select[0].outerHTML}
                            </td>
                      `
                $table.append(row)
                $table.show();
            });

            if(incomplete.length != 0){
                var $table = $('div#plex_parsed_csv table#incomplete')
                $.each(incomplete, function(index, movie){
                    var select = resolution_select;
                    select.children(`option`).removeAttr('selected')
                    select.children(`option[value="${movie['resolution']}"]`).attr('selected', 'selected');
                    if(movie['imdbid']){
                        id = movie['imdbid']
                    } else {
                        id = movie['tmdbid']
                    }

                    row = `<tr>
                                <td>
                                    <i class='fa fa-check-square checkbox', value='True'/>
                                    <span class='hidden data'>${JSON.stringify(movie)}</span>
                                </td>
                                <td class='file_location' data-original="${movie['file']}">
                                    ${movie['file']}
                                </td>
                                <td>
                                    ${movie['title']}
                                </td>
                                <td>
                                    <input type='text' class='input_imdbid', placeholder='tt0123456' value=${imdbid}></input>
                                </td>
                                <td class='resolution'>
                                    ${select[0].outerHTML}
                                </td>
                          `
                    $table.append(row)
                    $table.show();

                });
            }

            $('div#plex_parsed_csv').slideDown();
            $('div#thinker').fadeOut();
        });
    });

    $("button#plex_apply_remote").click(function(){
        var local = $('input#plex_local_path').val()
        var remote = $('input#plex_remote_path').val()

        $('div#plex_parsed_csv table td.file_location').each(function(index, elem){
            var $elem = $(elem);
            var new_path = $elem.text().replace(remote, local)
            $elem.text(new_path);
        })
    })

    $("button#plex_reset_remote").click(function(){
        $('div#plex_parsed_csv table td.file_location').each(function(index, elem){
            var $elem = $(elem);
            $elem.text($elem.attr('data-original'));
        })
    })

    $('span#plex_import').click(function(){
        var cancel = false;
        var movie_data = [];
        $('div#plex_parsed_csv table#complete tr').each(function(index, elem){
            var $row = $(elem);
            if(!is_checked($row.find('i.checkbox'))){
                return 'continue'
            }

            movie = JSON.parse($row.find('span.data').text())
            movie['finished_file'] = $row.find('td.file_location').text().trim()
            movie['resolution'] = $row.find('td.resolution select').val();
            movie_data.push(movie);
        })

        var corrected_movies = [];
        $('div#plex_parsed_csv table#incomplete tr').each(function(index, elem){
            var $row = $(elem);
            if(!is_checked($row.find('i.checkbox'))){
                return 'continue'
            }

            movie = JSON.parse($row.find('span.data').text())
            movie['finished_file'] = $row.find('td.file_location').text().trim();
            movie['imdbid'] = $row.find('input.input_imdbid').val();
            if(movie['imdbid'] == ''){
                highlight($row.find('input.input_imdbid'));
                cancel = true;
                return
            }
            movie['resolution'] = $row.find('td.resolution select').val();
            corrected_movies.push(movie);
        });

        if(corrected_movies.length == 0 && movie_data.length == 0){
            toastr.warning("All imports disabled.");
        }

        if(cancel){
            return false
        }

        $('div#plex_parsed_csv').slideUp();
        $('div#plex_import_results').slideDown();
        $('div#plex_wait_importing').slideDown();

        var $import_progress_text = $('div#plex_wait_importing span#import_progress_text');
        var $import_progress_bar = $('div#plex_wait_importing span.progress_bar');
        var $success_table = $('table#plex_import_success')
        var $error_table = $('table#plex_import_error')
        var last_response_len = false;
        $.ajax(url_base + '/ajax/import_plex_csv', {
            method: "POST",
            data: {"movie_data": JSON.stringify(movie_data), "corrected_movies": JSON.stringify(corrected_movies)},
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
                    var progress_percent = (r['progress'][0] / r['progress'][1]) * 100 + '%';
                    $import_progress_text.text(progress_text)
                    $import_progress_bar.width(progress_percent)
                    if(r['response'] === true){
                        $success_table.show()
                        var row = `<tr>
                                       <td>${r['movie']['title']}</td>
                                       <td>${r['movie']['imdbid']}</td>
                                   </tr>`
                        $success_table.append(row)
                    } else {
                        $error_table.show()
                        var row = `<tr>
                                       <td>${r['movie']['title']}</td>
                                       <td>${r['error']}</td>
                                   </tr>`
                        $error_table.append(row)
                    }
                }
            }
        })
        .done(function(data)
        {
            $("div#plex_wait_importing").slideUp();
            $('a#finished').slideDown();
        })
        .fail(function(data)
        {
            var err = data.status + ' ' + data.statusText
            toastr.error(err);
        });

    });


// General UI
    // set default state for pseudo checkboxes
    $("i.checkbox").each(function(){
        $this = $(this);
        if ($this.attr("value") == "True" ){
            $this.removeClass("fa-square-o");
            $this.addClass("fa-check-square");
        }
    });

    // toggle checkbox status
    $content.on("click", "i.checkbox", function(){
        $this = $(this);
        // turn on
        if( $this.attr("value") == "False" ){
            $this.attr("value", "True");
            $this.removeClass("fa-square-o");
            $this.addClass("fa-check-square");
        // turn off
        } else if ($this.attr("value") == "True" ){
            $this.attr("value", "False");
            $this.removeClass("fa-check-square");
            $this.addClass("fa-square-o");
        }
    });

    function is_checked(checkbox){
        // Turns value of checkbox "True"/"False" into bool
        // checkbox: object jquery object of checkbox <i>
        return (checkbox.attr("value") == "True")
    }

    function highlight(element){
        // Highlights empty or invalid inputs
        // element: object JQ object of input to highlight
        orig_bg = element.css("background-color");
        element.css("background-color", "#f4693b");
        element.delay(500).animate({"background-color": orig_bg}, 1000);
    }
})
