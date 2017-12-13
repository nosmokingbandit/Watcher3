$(document).ready(function(){
    var git_url = $("meta[name='git_url']").attr("content");

    // Init tooltips
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    })

    // set default state for pseudo checkboxes
    $("i.c_box").each(function(){
        $this = $(this);
        if ($this.attr("value") == "True" ){
            $this.removeClass("mdi-checkbox-blank-outline").addClass("mdi-checkbox-marked");
        }
    });

    // Set select option's values
    $("select").each(function(i, elem){
        var $this = $(elem);
        var val = $this.attr('value');
        $this.children("option[value='"+val+"']").prop('selected', true);

    });

    // toggle checkbox status on click
    $("body").on("click", "i.c_box", function(){
        $this = $(this);
        // turn on
        if( $this.attr("value") == "False" ){
            $this.attr("value", "True");
            $this.removeClass("mdi-checkbox-blank-outline").addClass("mdi-checkbox-marked");
        // turn off
        } else if ($this.attr("value") == "True" ){
            $this.attr("value", "False");
            $this.removeClass("mdi-checkbox-marked").addClass("mdi-checkbox-blank-outline");
        }
    });

    // Clear empty highlight on input
    $("body").on("focus", "input", function(){
        $(this).removeClass("empty");
    })

    // set up sortable
    init_sortables()
});

// Shared functions for saving settings
function save_settings(event, elem){
    event.preventDefault();
    var $this = $(elem);
    var $i = $this.find("i");

    $i.removeClass("mdi-content-save").addClass("mdi-circle-outline animated");

    var settings = _get_settings(); // This method is declared in each page's script.


    if(settings == false){
        $.notify({message: _("Please fill in all highlighted fields.")}, {type: "warning"})
        $i.removeClass("mdi-circle-outline animated").addClass("mdi-content-save");
        return false
    }

    $.post(url_base + "/ajax/save_settings", {
        "data": JSON.stringify(settings)
    })
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]})
        } else {
            $.notify({message: response['error']}, {type: "danger", delay: 0})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        $i.removeClass("mdi-circle-outline animated").addClass("mdi-content-save");
    });
}

function is_checked($checkbox){
    // Turns value of checkbox "True"/"False" into bool
    // checkbox: jquery object of checkbox <i>
    return ($checkbox.attr("value") == "True")
}

// Set up all drag/drop sortable lists
function init_sortables($sortables=false){
    if($sortables == false){
        var $sortables = $("ul.sortable");
    }

    $sortables.each(function(){
        $this = $(this);
        $lis = $this.children("li").get();

        $this.sortable({
            placeholderClass: "sortable_handle",
            items: ':not(.not_sortable)'
        })

        $lis.sort(function(a, b){
            var compa = parseInt($(a).data("sort"));
            var compb = parseInt($(b).data("sort"));
            return (compa < compb) ? -1 : (compa > compb) ? 1 : 0;
        })

        $.each($lis, function(idx, itm){
                $this.append(itm);
            });
    })
}
