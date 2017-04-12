$(document).ready(function(){
    var url_base = $("meta[name='url_base']").attr("content");
    var $movies = $('table#movie_table tr:not(:first)');

    $('button#select_all').click(function(){
        $movies.each(function(i, elem){
            var $elem = $(elem);
            var $chk = $elem.find('i.checkbox')
            $chk.attr("value", "True");
            $chk.removeClass('fa-square-o');
            $chk.addClass('fa-check-square');
        })
    });

    $('button#de_select_all').click(function(){
        $movies.each(function(i, elem){
            var $elem = $(elem);
            var $chk = $elem.find('i.checkbox')
            $chk.attr("value", "False");
            $chk.removeClass('fa-check-square');
            $chk.addClass('fa-square-o');
        })
    });

    $('button#invert_selection').click(function(){
        $movies.each(function(i, elem){
            var $elem = $(elem);
            var $chk = $elem.find('i.checkbox')
            if( $chk.attr("value") == "False"){
                $chk.attr("value", "True");
                $chk.removeClass('fa-square-o');
                $chk.addClass('fa-check-square');
            // turn off
            } else if ($chk.attr("value") == "True"){
                $chk.attr("value", "False");
                $chk.removeClass('fa-check-square');
                $chk.addClass('fa-square-o');
            }
        })
    });

    $('button#metadata_update').click(function(){
        var checked = get_checked_movies();
        if(checked.length == 0){
            toastr.warning('No movies selected');
            return
        }
        var grammar = (checked.length == 1 ? 'movie' : 'movies');

        swal({
            title: "Confirm Metadata Update",
            text: `Watcher will update metadata for ${checked.length} ${grammar}`,
            type: "",
            html: true,
            showCancelButton: true,
            imageUrl: "",
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Do it",
            closeOnConfirm: false,
            showLoaderOnConfirm: true,
        }, function(){
            $.post(url_base+"/ajax/manager_update_metadata", {'movies': JSON.stringify(checked)})
            .done(function(r){
                response = JSON.parse(r);

                if(response['response'] == true){
                    swal({
                        title: "Metadata Update Complete",
                        text: `Metadata updated for ${checked.length} ${grammar}<br/>
                               Refresh page to see updated metadata`,
                        type: "success",
                        showCancelButton: false,
                        imageUrl: "",
                        confirmButtonColor: "#4CAF50",
                        confirmButtonText: "Neat",
                        closeOnConfirm: true,
                    })
                } else {

                    var $errors = $(`<table id="errors"></table>`);
                    $.each(response['errors'], function(i, d){

                        var row = `<tr>
                                    <td> ${d['imdbid']} </td>
                                    <td> ${d['error']} </td>
                                   </tr>`;
                        $errors.append(row);
                    })

                    var err = $errors[0].outerHTML;

                    swal({
                        title: "Movies Reset Error",
                        text: `The following errors occurred while updating metadata:<br/>
                               <br/>
                               ${err}`,
                        type: "error",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#555",
                        confirmButtonText: "Bummer",
                        closeOnConfirm: true,
                    })
                }
            })
        });
    });

    $('button#quality').click(function(){
        var checked = get_checked_movies();
        if(checked.length == 0){
            toastr.warning('No movies selected');
            return
        }
        var grammar = (checked.length == 1 ? 'movie' : 'movies');
        var quality = $('select#select_quality').val();
        swal({
            title: "Confirm Quality Profile",
            text: `Watcher will change the quality profile for ${checked.length} ${grammar} to <b>${quality}</b>`,
            type: "",
            html: true,
            showCancelButton: true,
            imageUrl: "",
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Do it",
            closeOnConfirm: false,
            showLoaderOnConfirm: true,
        }, function(){
            $.post(url_base+"/ajax/manager_change_quality", {'movies': JSON.stringify(checked), 'quality': quality})
            .done(function(r){
                response = JSON.parse(r);

                if(response['response'] == true){
                    swal({
                        title: "Quality Change Complete",
                        text: `Quality Profile updated for ${checked.length} ${grammar}<br/>
                               Refresh page to see updated profile`,
                        type: "success",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#4CAF50",
                        confirmButtonText: "Swell",
                        closeOnConfirm: true,
                    })
                } else {

                    var $errors = $(`<table id="errors"></table>`);
                    $.each(response['errors'], function(i, d){

                        var row = `<tr>
                                    <td> ${d['imdbid']} </td>
                                    <td> ${d['error']} </td>
                                   </tr>`;
                        $errors.append(row);
                    })

                    var err = $errors[0].outerHTML;

                    swal({
                        title: "Quality Change Error",
                        text: `The following errors occurred while changing Quality Profiles:<br/>
                               <br/>
                               ${err}`,
                        type: "error",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#555",
                        confirmButtonText: "Bummer",
                        closeOnConfirm: true,
                    })
                }
            })
        });
    });

    $('button#remove').click(function(){
        var checked = get_checked_movies();
        if(checked.length == 0){
            toastr.warning('No movies selected');
            return
        }
        var grammar = (checked.length == 1 ? 'movie' : 'movies');
        swal({
            title: "Confirm Removal",
            text: `Watcher will remove ${checked.length} ${grammar} from the library<br/>
                   This will not remove movie files <br/>
                   This cannot be undone`,
            type: "",
            html: true,
            showCancelButton: true,
            imageUrl: "",
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Do it",
            closeOnConfirm: false,
            showLoaderOnConfirm: true,
        }, function(){
            $.post(url_base+"/ajax/manager_remove_movies", {'movies': JSON.stringify(checked)})
            .done(function(r){
                response = JSON.parse(r);
                if(response['response'] == true){
                    swal({
                        title: "Movies Removed",
                        text: `${checked.length} ${grammar} removed from library<br/>
                               Refresh page to see updated list`,
                        type: "success",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#4CAF50",
                        confirmButtonText: "Cool",
                        closeOnConfirm: true,
                    })
                } else {

                    var $errors = $(`<table id="errors"></table>`);
                    $.each(response['errors'], function(i, imdbid){

                        var row = `<tr>
                                    <td> ${d['imdbid']} </td>
                                   </tr>`;
                        $errors.append(row);
                    })

                    var err = $errors[0].outerHTML;

                    swal({
                        title: "Movie Removal Errors",
                        text: `Errors occurred while removing the following movies:<br/>
                               <br/>
                               ${err}
                               <br/>
                               Check your logs for more information`,
                        type: "error",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#555",
                        confirmButtonText: "Lame",
                        closeOnConfirm: true,
                    })
                }
            })
        });
    });

    $('button#reset').click(function(){
        var checked = get_checked_movies();
        if(checked.length == 0){
            toastr.warning('No movies selected');
            return
        }
        var grammar = (checked.length == 1 ? 'movie' : 'movies');
        swal({
            title: "Confirm Movie Reset",
            text: `Watcher will reset ${checked.length} ${grammar}<br/><br/>
                   This will: <br/><br/>
                   <ul style='text-align: left; margin: 0 0 0 2em ;'>
                     <li> • Remove all <b>Search Results</b> including <i>Import</i> results</li>
                     <li> • Set the <b>Quality Profile</b> to <i>Default</i></li>
                     <li> • Restore the movies' <b>Status</b> to <i>Wanted</i></li>
                   </ul>
                   </br>
                   This cannot be undone.
                   `,
            type: "",
            html: true,
            showCancelButton: true,
            imageUrl: "",
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Do it",
            closeOnConfirm: false,
            showLoaderOnConfirm: true,
        }, function(){
            $.post(url_base+"/ajax/manager_reset_movies", {'movies': JSON.stringify(checked)})
            .done(function(r){
                response = JSON.parse(r);
                if(response['response'] == true){
                    swal({
                        title: "Movies Reset",
                        text: `${checked.length} ${grammar} reset<br/>
                               Refresh page to see updated list`,
                        type: "success",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#4CAF50",
                        confirmButtonText: "Groovy",
                        closeOnConfirm: true,
                    })
                } else {

                    var $errors = $(`<table id="errors"></table>`);
                    $.each(response['errors'], function(i, d){

                        var row = `<tr>
                                    <td> ${d['imdbid']} </td>
                                    <td> ${d['error']} </td>
                                   </tr>`;
                        $errors.append(row);
                    })

                    var err = $errors[0].outerHTML;

                    swal({
                        title: "Movies Reset Error",
                        text: `The following errors occurred while resetting movies:<br/>
                               <br/>
                               ${err}`,
                        type: "error",
                        showCancelButton: false,
                        imageUrl: "",
                        html: true,
                        confirmButtonColor: "#555",
                        confirmButtonText: "Bummer",
                        closeOnConfirm: true,
                    })
                }
            })
        });
    });

    /* toggle check box status */
    $('i.checkbox').click(function(){
        // turn on
        var $this = $(this)
        if( $this.attr("value") == "False"){
            $this.attr("value", "True");
            $this.removeClass('fa-square-o');
            $this.addClass('fa-check-square');
        // turn off
        } else if ($this.attr("value") == "True"){
            $this.attr("value", "False");
            $this.removeClass('fa-check-square');
            $this.addClass('fa-square-o');
        }
    });

    function get_checked_movies(){
        var a = [];
        $('table#movie_table tr:not(:first)').each(function(i, elem){
            var $elem = $(elem);
            if($elem.find('i.checkbox').attr('value') == "True"){
                a.push(JSON.parse($elem.find('span.data').text()));
            }
        })
        return a
    }
});
