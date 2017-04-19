$(document).ready(function(){
    var url_base = $("meta[name='url_base']").attr("content");

/* Database Management */
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
                        html: true,
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

/* Charts */
var stats = JSON.parse($('div.stats').text());

    Morris.Donut({
        element: $('div#chart_status .chart'),
        data: stats['status'],
        colors: ['#4CAF50', '#CDDC39', '#00BCD4', '#FF9800'],
        labelColor: '#ccc',
        labelSize: '24px'
    })

    Morris.Donut({
        element: $('div#chart_qualities .chart'),
        data: stats['qualities'],
        colors: ['#03A9F4', '#673AB7', '#F44336', '#FF9800', '#FFEB3B', '#4CAF50'],
        labelColor: '#ccc',
        labelSize: '24px'
    })

    Morris.Bar({
        element: $('div#chart_years .chart'),
        data: stats['years'],
        xkey: 'year',
        ykeys: ['value'],
        labels: ['Movies'],
        barColors: ['#ccc'],
    })

    Morris.Line({
        element: $('div#chart_added .chart'),
        data: stats['added_dates'],
        xkey: 'added_date',
        ykeys: ['value'],
        labels: ['Movies'],
        lineColors: ['#ccc'],
        pointFillColors: ['#080f18'],
        pointStrokeColors: ['#ccc'],
        xLabels: 'month',
        smooth: false
    })

    $('svg text').css('font-family', 'Raleway')


/* ui */
    $('div#_stats').hide();
    $('div#_database').hide();

    var sub_page = window.location.hash.slice(1);

    if(sub_page){
        $('div#_'+sub_page).show();
        $('ul#subnav a').removeClass('active');
        console.log('a[href="#'+sub_page+'"]')
        $('ul#subnav a[href="#'+sub_page+'"]').addClass('active')
    } else {
        $('div#_stats').show();
    }

    $('ul#subnav a').click(function(e){
        $this = $(this);
        if($this.hasClass('active')){
            return false
        } else {
            $('ul#subnav a.active').removeClass('active');
            $this.addClass('active');
            var page = $this.attr('page');
            $('div#content > div').slideUp();
            $('div#'+page).slideDown();
        }
    })

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

});
