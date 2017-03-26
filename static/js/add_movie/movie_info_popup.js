$(document).ready(function() {
    var url_base = $("meta[name='url_base']").attr("content");

    /* set up sortable */
    $(function () {
        $( "ul.sortable" ).sortable();
        $( "ul.sortable" ).disableSelection();
    });

    $( "ul.sortable" ).sortable({
        cancel: "span.not_sortable"
    });

    /* set order for sortable items */
    $("ul#resolution li").each(function () {
        $(this).siblings().eq($(this).attr('sort')).after($(this));
    });
    $("ul#sources li").each(function () {
        $(this).siblings().eq($(this).attr('sort')).after($(this));
    });

    /* set default state for pseudo checkboxes */
    $('i.checkbox').each(function(){
       if ( $(this).attr("value") == "True" ){
           $(this).removeClass('fa-square-o');
           $(this).addClass('fa-check-square');
       }
    });

    /* toggle check box status */
    $('i.checkbox').click(function(){
        // turn on
        if( $(this).attr("value") == "False"){
            $(this).attr("value", "true");
            $(this).removeClass('fa-square-o');
            $(this).addClass('fa-check-square');
        // turn off
        } else if ( $(this).attr("value") == "True"){
            $(this).attr("value", "false");
            $(this).removeClass('fa-check-square');
            $(this).addClass('fa-square-o');
        }
    });

    $('i#button_add').click(function(e){
        $this = $(this);
        $this.animate({width:'toggle'}, 750);
        $('div#quality').fadeIn(750)

    e.preventDefault();
    });

    $('i#button_save').click(function(e){
        $this = $(this);
        $this.removeClass('fa-save');
        $this.addClass('fa-circle faa-burst animated');

        quality = $('select#quality_profile').val();

        // because we are pulling a string out of the div we need to make it an object, then have json turn it into a string
        data = $.parseJSON( $('div#hidden_data').text() );
        data['quality'] = quality;
        data = JSON.stringify(data);

        $.post(url_base + "/ajax/add_wanted_movie", {"data": data})
        .done(function(r){
            response = JSON.parse(r)

            if(response['response'] == true){
                toastr.success(response['message']);
            } else {
                toastr.error(response['error']);
            };
            $this.addClass('fa-save');
            $this.removeClass('fa-circle faa-burst animated');
            $('div#quality').fadeOut();
        });

    e.preventDefault();
    })
});
