window.addEventListener("DOMContentLoaded", function(){
    $stepper = document.getElementById('stepper');
    $progress = $("div.progress");

    $progress = document.getElementById('progress_bar');
    $progress_bar = $progress.children[0];
    $progress_text = $progress.children[1];

    $source_select = document.querySelector('template#source_select').content.children[0];
    $quality_select = document.querySelector('template#quality_select').content.children[0];

    // Clear empty highlight on input
    $("body").on("click", "input", function(){
        $(this).removeClass("empty");
    })

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

});

function is_checked($checkbox){
    // Turns value of checkbox "True"/"False" into bool
    // checkbox: jquery object of checkbox <i>
    return $checkbox.getAttribute("value") == "True"
}


function set_stepper(value){
    each($stepper.children, function(pill){
        if(pill.getAttribute('target') == value){
            pill.classList.add('active');
        } else {
            pill.classList.remove('active');
        }
    })
}
