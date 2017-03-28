$(document).ready(function() {
    var url_base = $("meta[name='url_base']").attr("content");
    var directory = "";
    var resolutions = JSON.parse($('#resolution_list').text());
    resolution_select = $("<select class='input_resolution'></select>");
    $.each(resolutions, function(i, v){
        resolution_select.append(`<option value=${v}>${v}</option>`)
    })

    var $content = $("div#content");
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
        $.ajax(url_base + '/ajax/scan_library', {
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
            $('span#import').slideDown();
        })
        .fail(function(data)
        {
            var err = data.status + ' ' + data.statusText
            toastr.error(err);
        });
    });

    function render_movie(response){
        // Renders movie output from scanner
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
        }else if(response['response'] == 'complete'){
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

            movie_data = JSON.stringify(movie_data)
            corrected_movies = JSON.stringify(corrected_movies);

            if(corrected_movies === false){
                return false
            }

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
                source = $this.find("select.input_resolution").val();
                metadata['resolution'] = source;
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
        $.ajax(url_base + '/ajax/submit_import', {
            method: "POST",
            data: {"movie_data":movie_data, "corrected_movies": corrected_movies},
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
                        $imporerror_tablet_error.show()
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
            $('div#wait_importing span#import_progress').text('');
            $("div#wait_importing").slideUp();
            $('a#finished').slideDown();
        })
        .fail(function(data)
        {
            var err = data.status + ' ' + data.statusText
            toastr.error(err);
        });
    }

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
