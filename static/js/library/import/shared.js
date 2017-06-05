$(document).ready(function(){
    $progress = $("div.progress");
    $progress_bar = $("div.progress > div.progress-bar");
    $progress_text = $("span#progress_text")

    source_select = $("textarea#source_select")[0].innerText;
    quality_select = $("textarea#quality_select")[0].innerText;

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
    return ($checkbox.attr("value") == "True")
}