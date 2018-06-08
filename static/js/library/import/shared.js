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

function select_all(table){
    // table (str): table id to apply select to
    event.preventDefault();
    var $checkboxes = document.querySelectorAll(`div#${table} > table i.c_box`);
    each($checkboxes, function(checkbox){
        checkbox.setAttribute('value', 'False');
        checkbox_switch({target: checkbox});
    });
}

function select_none(table){
    // table (str): table id to apply select to
    event.preventDefault();
    var $checkboxes = document.querySelectorAll(`div#${table} > table i.c_box`);
    each($checkboxes, function(checkbox){
        checkbox.setAttribute('value', 'True');
        checkbox_switch({target: checkbox});
    });
}

function select_inverse(table){
    // table (str): table id to apply select to
    event.preventDefault();
    var $checkboxes = document.querySelectorAll(`div#${table} > table i.c_box`);
    each($checkboxes, function(checkbox){
        checkbox_switch({target: checkbox});
    });
}

function checkbox_switch(event){
    var checkbox = event.target;
    // turn on
    if(checkbox.getAttribute("value") == "False"){
        checkbox.setAttribute("value", "True");
        checkbox.classList.remove("mdi-checkbox-blank-outline");
        checkbox.classList.add("mdi-checkbox-marked");
    // turn off
    } else if(checkbox.getAttribute("value") == "True"){
        checkbox.setAttribute('value', 'False');
        checkbox.classList.remove("mdi-checkbox-marked");
        checkbox.classList.add("mdi-checkbox-blank-outline");
    }
};
