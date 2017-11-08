$(document).ready(function(){
    $tasks_table = $("table#tasks > tbody");
    server_time = $("meta[name='server_time']").attr("content");
    tasks = JSON.parse($("meta[name='tasks']").attr("content"));


    $.each(tasks, function(i, task){
        $tasks_table.append(_render_task_row(task));
    })

    $restore_modal = $("div#modal_restore_backup");
    var restore_modal_html = $restore_modal[0].innerHTML;

    $restore_modal.on('hidden.bs.modal', function(){
        $restore_modal.html(restore_modal_html);
    })


});

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
                <td class="center"><i class="mdi mdi-play-circle task_execute" onclick="execute_task(event, this, '${task["name"]}')"></i></td>
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

function create_backup(event, elem){
    event.preventDefault();
    var $btns = $("div#modal_create_backup a.btn");
    var $thinker = $("div#modal_create_backup div.thinker_small");

    $btns.addClass("disabled");

    $thinker.slideDown();

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
        $btns.removeClass("disabled");
        $thinker.slideUp();
    });
}

function _restore_zip_selected(elem){
    var v = $(elem).val()
    $("input#zip_file_input").val(v);
    if(v){
        $("a#submit_restore_zip").removeClass("disabled");
    } else {
        $("a#submit_restore_zip").addClass("disabled");
    }
}

function upload_restore_zip(event, elem){
    event.preventDefault();
    var $this = $(elem);
    var $input = $("#zip_file");
    var $progress_bar = $restore_modal.find("div.progress-bar");
    var $modal_tc = $restore_modal.find(".modal-body > div.text_content");
    var $title_text = $restore_modal.find("div.modal-header > .modal-title");
    var $thinker_small = $restore_modal.find("div.modal-body div.thinker_small");
    var oc = $this.attr("onclick");
    $this.attr("onclick", "");


    $input.liteUploader({
        script: url_base + "/ajax/restore_backup",
    })
    .on("lu:errors", function (e, errors) {
        if(errors[0]["errors"][0]["type"] == "type"){
            $.notify({message: _("Select a ZIP file.")}, {type: "warning"})
        } else {
            $.each(errors[0]["errors"], function(i, err){
                $.notify({message: `Error: ${err["type"]}`}, {type: "warning"})
            })
        }
    })
    .on("lu:before", function(){
        $modal_tc.slideUp();
        $restore_modal.find(".modal-body > div.progress").slideDown();
        $title_text.text(_("Uploading Restore Zip."));
        $thinker_small.slideDown();
    })
    .on("lu:progress", function (e, state) {
        $progress_bar.width(state.percentage + "%");
        if(state.percentage == 100){
            $title_text.text(_("Restoring Backup."));
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

    $input.data("liteUploader").startUpload();

    return
}

function execute_task(event, elem, name){
    event.preventDefault();

    var $this = $(elem);
    if($this.hasClass("disabled")){
        return
    }
    var $tr = $this.closest("tr");
    var $btns = $("i.task_execute");

    $btns.addClass("disabled");
    $this.attr("onclick", "");
    $this.removeClass("mdi-play-circle").addClass("mdi-circle-outline animated");

    $.post(url_base + "/ajax/manual_task_execute", {name: name})
    .done(function(response){
        var t = tasks[name];
        t["last_execution"] = response["last_execution"]

        var row = _render_task_row(t);
        $tr[0].innerHTML = row;

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
        $this.removeClass("mdi-circle-outline animated").addClass("mdi-play-circle");
        $btns.removeClass("disabled");
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
