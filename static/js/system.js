window.addEventListener("DOMContentLoaded", function(){
    $tasks_table = document.querySelector("table#tasks > tbody");
    server_time = document.querySelector('meta[name="server_time"]').content;
    tasks = JSON.parse(document.querySelector('meta[name="tasks"]').content);

    $button_begin_restore = document.querySelector("button#submit_restore_zip");

    $.each(tasks, function(i, task){
        $tasks_table.innerHTML += _render_task_row(task);
    })

    $restore_modal = document.getElementById("modal_restore_backup");
    var restore_modal_html = $restore_modal.innerHTML;

    $restore_modal.addEventListener('hidden.bs.modal', function(){
        $restore_modal.innerHTML = restore_modal_html;
    })

    each(document.querySelectorAll('input[type="time"]'), function(input){
        var hr = input.dataset.hour.toString().padStart(2, 0);
        var min = input.dataset.minute.toString().padStart(2, 0);
        input.value = hr + ':' + min;
    })

});

function _get_settings(){

    var settings = {};
    settings["FileManagement"] = {};
    var blanks = false;

// FILEMANAGEMENT
    var required_fields = []

    each(document.querySelectorAll("form[data-category='filemanagement'] i.c_box"), function(checkbox){
        settings['FileManagement'][checkbox.id] = is_checked(checkbox);
    })

    if(settings['scanmissingfiles']){
        required_fields.push("scanmissinghour", "scanmissingmin");
    }

    each(document.querySelector("form[data-category='filemanagement']").querySelectorAll('input, select'), function(input){
        if(input.value == "" && required_fields.includes(input.id)){
            input.classList.add('border-danger');
            blanks = true;
            return
        } else if(input.id == 'scanmissingtime'){
            var [hour, min] = input.value.split(":").map(function(item){
                return parseInt(item);
            });
            settings['FileManagement']['scanmissinghour'] = hour;
            settings['FileManagement']['scanmissingmin'] = min;
            return
        }

        settings['FileManagement'][input.id] = parse_input(input);
    })

    if(blanks == true){
        return false;
    };
    return {"System": settings}
}

function _render_task_row(task){
    /* renders row in task table
    task (dict): json object of task info

    Returns string html for row
    */

    var le = Date.parse(task["last_execution"]) / 1000;

    var next = le + task["interval"]

    while(next < server_time){
        next += task["interval"];
    }

    if(task["enabled"]){
        var next = time_difference(server_time, next);
        var enabled = "<i class='mdi mdi-check'></i>";
    } else {
        var next = "--";
        var enabled = "";
    };

    var le = time_difference(server_time, le);

    var interval = interval_string(task["interval"]);

    var row = `<tr>
                <td class="center">${enabled}</td>
                <td>${task["name"]}</td>
                <td>${interval}</td>
                <td>${le}</td>
                <td>${next}</td>
                <td class="center">
                    <i class="mdi mdi-play-circle task_execute" onclick="execute_task(event, this, '${task["name"]}')"></i>
                </td>
            </tr>`
    return row
}

function interval_string(seconds){
    /* Converts seconds to a readable time string
    seconds (int): seconds to convert to X minutes, X hours, etc

    Returns string
    */

    var times = ['seconds', 'minutes', 'hours']

    if(seconds % 3600 == 0){
        return seconds / 3600 + " Hours";
    } else if(seconds % 60 == 0){
        return seconds / 60 + " Minutes";
    } else {
        return seconds + " Seconds";
    };
}

function time_string(time){
    /* Converts unix timestamp to human-readable time format 2017-01-01 12:05:55
    time (int): seconds in unix time

    returns string
    */
    var date = new Date(time);
    var year = date.getFullYear();
    var month = date.getMonth() + 1;
    var day = date.getDate();
    var hour = date.getHours();
    var min = date.getMinutes();
    var sec = date.getSeconds();
    month = (month < 10 ? "0" : "") + month;
    day = (day < 10 ? "0" : "") + day;
    hour = (hour < 10 ? "0" : "") + hour;
    min = (min < 10 ? "0" : "") + min;
    sec = (sec < 10 ? "0" : "") + sec;

    return `${year}-${month}-${day} ${hour}:${min}:${sec}`
}

function create_backup(event, button){
    event.preventDefault();
    var $btns = document.querySelectorAll('div#modal_create_backup button');
    var $thinker = document.querySelector("div#modal_create_backup div.thinker_small");

    each($btns, function(button){
        button.setAttribute('disabled', true);
    })

    $thinker.style.maxHeight = "100%";

    $.post(url_base + "/ajax/create_backup", {})
    .done(function(response){
        if(response["response"] == true){
            $.notify({message: response["message"]}, {delay: 0})
        } else {
            $.notify({message: `${response['error']}`}, {type: "danger", delay: 0})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        each($btns, function(button){
            button.removeAttribute('disabled');
        })

        $thinker.style.maxHeight = "0%";
    });
}

function _restore_zip_selected(input){
    // Sets text input and enabled buttons when restore zip is selected
    var v = input.value;
    document.querySelector("input#zip_file_input").value = v;
    if(v){
        $button_begin_restore.removeAttribute("disabled");
    } else {
        $button_begin_restore.setAttribute("disabled", true);
    }
}

function upload_restore_zip(event, button){
    // Starts restoration process
    event.preventDefault();


    var $input = document.getElementById("zip_file");
    var $progress_bar = $restore_modal.querySelector("div.progress-bar");
    var $modal_tc = $restore_modal.querySelector(".modal-body > div.text_content");
    var $title_text = $restore_modal.querySelector("div.modal-header > .modal-title");

    var $thinker = document.querySelector("div#modal_create_backup div.thinker_small");

    button.setAttribute('disabled', true);

    $($input).liteUploader({
        script: url_base + "/ajax/restore_backup",
    })
    .on("lu:errors", function (e, errors) {
        if(errors[0]["errors"][0]["type"] == "type"){
            $.notify({message: _("Select a ZIP file.")}, {type: "warning"})
        } else {
            each(errors[0]['errors'], function(err){
                $.notify({message: `Error: ${err["type"]}`}, {type: "warning"})
            })
        }
    })
    .on("lu:before", function(){
        $modal_tc.style.maxHeight = '0%';
        $restore_modal.querySelector("div.progress").style.maxHeight = '100%';
        $title_text.innerText = _("Uploading Restore Zip.");
        $thinker.style.maxHeight = '100%';
    })
    .on("lu:progress", function (e, state) {
        $progress_bar.style.width = (state.percentage + "%");
        if(state.percentage == 100){
            $title_text.innerText = _("Restoring Backup.");
        }
    })
    .on("lu:success", function (e, response) {
        response = JSON.parse(response);
        if(response["response"] == true){
            $.notify({message: "Restore finished, restarting..."});
            setTimeout(function(){
                window.location = url_base + "/system/restart?e=false";
            }, 1000);
        } else {
            $.notify({message: response["error"]}, {type: "warning"})
        }
    })
    .on("lu:fail", function (e, data) {
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    });

    $($input).data("liteUploader").startUpload();

    return
}

function execute_task(event, elem, name){
    event.preventDefault();
    var $this = $(elem);

    if(elem.classList.contains("disabled")){
        return
    }
    var $tr = elem.parentElement.parentElement;
    var $btns = document.querySelectorAll("i.task_execute");

    each($btns, function(b, i){
        b.classList.add("disabled");
    });
    elem.classList.remove("mdi-play-circle");
    elem.classList.add("mdi-circle");
    elem.classList.add("animated");

    $.post(url_base + "/ajax/manual_task_execute", {name: name})
    .done(function(response){
        var t = tasks[name];
        t["last_execution"] = response["last_execution"]

        $tr.innerHTML = _render_task_row(t);

        if(response["response"] == true){
            $.notify({message: response["message"]})
            $.each(response["notifications"], function(i, notif){
                notif[1]["onClose"] = remove_notif;
                var n = $.notify(notif[0], notif[1]);
                n["$ele"].attr("data-index", notif[1]["index"]);
            });
        } else {
            $.notify({message: response["error"]}, {type: "danger", delay: 0})
        }
    })
    .fail(function(data){
        var err = data.status + ' ' + data.statusText
        $.notify({message: err}, {type: "danger", delay: 0});
    })
    .always(function(){
        elem.classList.remove("mdi-circle");
        elem.classList.remove("animated");
        elem.classList.add("mdi-play-circle");
        each($btns, function(b, i){
            b.classList.remove("disabled");
        });
    });

}

function time_difference(now, time){
    /* Returns an english relative-time string ie '3 hours ago'
    now (int): current epoch time
    time (int): time in future/past to find difference for

    Use server time for now since all times are relative to the server

    Returns string
    */

    var diff = time - now;
    if(diff > 0){
        var a = "";
    } else {
        var a = " ago";
    };

    diff = Math.abs(diff);

    if(diff < spmin){
         var t = diff + ' seconds';
    } else if(diff < sphr){
         var t = Math.round(diff/spmin) + ' minutes';
    } else if(diff < spd ){
         var t = Math.round(diff/sphr ) + ' hours';
    } else {
        var t = Math.round(diff/spd) + ' days';
    }
    return t + a;
}

/* Delcaring some time vars */
var spmin = 60;
var sphr = spmin * 60;
var spd = sphr * 24;
