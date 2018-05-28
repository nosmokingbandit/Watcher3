window.addEventListener('DOMContentLoaded', function(){
    // Init tooltips
    $('[data-toggle="tooltip"]').tooltip()

    // set default state for pseudo checkboxes
    each(document.querySelectorAll('i.c_box'), function(checkbox, i){
        if(checkbox.getAttribute('value') == 'True'){
            checkbox.classList.remove('mdi-checkbox-blank-outline');
            checkbox.classList.add('mdi-checkbox-marked')
        }
    })

    // Set select option's values
    each(document.getElementsByTagName('select'), function(select, i){
        var s = select.querySelector('option[value="'+select.getAttribute('value')+'"]')
        if(s){
            s.setAttribute('selected', true);
        }
    })

    document.body.addEventListener('click', function(event){
        if(event.target.tagName == 'I' && event.target.classList.contains('c_box')){
            // turn on;
            if(event.target.getAttribute('value') == 'False'){
                event.target.setAttribute('value', 'True');
                event.target.classList.remove('mdi-checkbox-blank-outline');
                event.target.classList.add('mdi-checkbox-marked');
            // turn off;
            } else if(event.target.getAttribute('value') == 'True'){
                event.target.setAttribute('value', 'False');
                event.target.classList.remove('mdi-checkbox-marked');
                event.target.classList.add('mdi-checkbox-blank-outline');
            }
        }
    })

    // Clear empty highlight on input
    $('body').on('focus', 'input', function(){
        $(this).removeClass('border-danger');
    })

    // set up sortable
    init_sortables()
});

// Shared functions for saving settings
function save_settings(event, elem){
    event.preventDefault();
    var $i = elem.querySelector('i');

    $i.classList.remove('mdi-content-save');
    $i.classList.add('mdi-circle', 'animated');


    var settings = _get_settings(); // This method is declared in each page's script.

    if(settings == false){
        $.notify({message: _('Please fill in all highlighted fields.')}, {type: 'danger'})
        $i.classList.remove('mdi-circle',  'animated');
        $i.classList.add('mdi-content-save');
        return false
    }

    $.post(url_base + '/ajax/save_settings', {
        'data': JSON.stringify(settings)
    })
    .done(function(response){
        if(response['response'] == true){
            $.notify({message: response['message']})
        } else {
            $.notify({message: response['error']}, {type: 'danger', delay: 0})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: 'danger', delay: 0});
    })
    .always(function(){
        $i.classList.remove('mdi-circle', 'animated');
        $i.classList.add('mdi-content-save');
    });
}

function is_checked(checkbox){
    // Turns value of checkbox 'True'/'False' into bool
    // checkbox: html node of checkbox <i>
    return (checkbox.getAttribute('value') == 'True')
}

function parse_input(input){
    // Parses input elements into their respective type while
    //     modifying for min/max values of numbers, etc
    // input: html node of input
    //
    // Returns declared type of input

    if(input.type == 'number'){
        var min = parseInt(input.min || 0);
        var val = Math.max(parseInt(input.value), min);
        return val || min;
    } else {
        return input.value;
    }
}

// Set up all drag/drop sortable lists
function init_sortables($sortables=false){
    // $sortables jquery objects to apply sortable to
    // if sortables isn't passed will use all ul.sortable in DOM
    if($sortables == false){
        var $sortables = $('ul.sortable');
    }

    $sortables.each(function(){
        $this = $(this);
        $lis = $this.children('li').get();

        $this.sortable({
            placeholderClass: 'sortable_handle',
            items: ':not(.not_sortable)'
        })

        $lis.sort(function(a, b){
            var compa = parseInt($(a).data('sort'));
            var compb = parseInt($(b).data('sort'));
            return (compa < compb) ? -1 : (compa > compb) ? 1 : 0;
        })

        $.each($lis, function(idx, itm){
                $this.append(itm);
            });
    })
}
