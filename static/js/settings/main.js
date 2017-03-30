$(document).ready(function () {
    var url_base = $("meta[name='url_base']").attr("content");
    var git_url = $("meta[name='git_url']").attr("content");

/* Shared */

    // set default state for pseudo checkboxes
    $("i.checkbox").each(function(){
        $this = $(this);
        if ($this.attr("value") == "True" ){
            $this.removeClass("fa-square-o")
            $this.addClass("fa-check-square");
        }
    });

    // toggle checkbox status
    $("div#content").on("click", "i.checkbox", function(){
        $this = $(this);
        // turn on
        if( $this.attr("value") == "False" ){
            $this.attr("value", "True");
            $this.removeClass("fa-square-o")
            $this.addClass("fa-check-square");
        // turn off
        } else if ($this.attr("value") == "True" ){
            $this.attr("value", "False");
            $this.removeClass("fa-check-square");
            $this.addClass("fa-square-o")
        }
    });

    // set up sortable
    init_sortables()

/* Server */

    // Generate new api key
    $("div.server i#generate_new_key").click(function(){
        var key = new_api_key(32);
        $("input#apikey").val(key);
    })

    new_api_key = function(length) {
        var text = "";
        var possible = "abcdef0123456789";
        for(var i = 0; i < length; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }

    // shutdown & restart
    $("div.server span#restart").click(function(){
        swal({
            title: "Restart Watcher?",
            text: "",
            type: "",
            showCancelButton: true,
            imageUrl: "",
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Restart",
            closeOnConfirm: true
        }, function(){
            window.location = url_base + "/restart";
        });
    });

    $("div.server span#shutdown").click(function(){
        swal({
            title: "Shut Down Watcher?",
            text: "",
            type: "",
            showCancelButton: true,
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Shut Down",
            closeOnConfirm: true
        }, function(){
            window.location = url_base + "/shutdown";
        });
    });

    // check for updates
    $("div.server span#update_check").click(function(){
        $this = $(this);
        $i = $this.find(":first");

        $i.removeClass("fa-arrow-circle-up");
        $i.addClass("fa-circle faa-burst animated");

        $.post(url_base + "/ajax/update_check", {})
        .done(function(r){

            response = JSON.parse(r);
            if(response["status"] == "current"){
                toastr.info("No updates available.");
            } else if(response["status"] == "error"){
                toastr.warning(response["error"]);
            } else if(response["status"] == "behind"){

                if(response["behind_count"] == 1){
                    title = response["behind_count"] + " Update Available";
                } else {
                    title = response["behind_count"] + " Updates Available";
                };

                compare = git_url + "/compare/" + response["local_hash"] + "..." + response["new_hash"]

                body = "Click <a href='update_now'><u>here</u></a> to update now. <br/> Click <a href=" + compare + " target=_blank><u>here</u></a> to view changes."


                toastr.info(body, title, {closeButton:true,
                                          timeOut: 0,
                                          extendedTimeOut: 0,
                                          tapToDismiss: 0
                                          });

            }
        $i.addClass("fa-arrow-circle-up");
        $i.removeClass("fa-circle faa-burst animated");

        })
    });

    // Install updates
    function update_now(){
        $.post(url_base + "/ajax/update_now", {"mode": "set_true"})
        .done(function(){
            window.location = url_base + "/update";
        });
    };

/* Providers */

    // Add new rows
    $("div.providers i#add_newznab_row").click(function (){
        var row = `
        <li class='newznab_indexer'>
            <i class='fa fa-square-o newznab_check checkbox' value='False'/>
            <input class='newznab_url' placeholder=' http://indexer.url' type='text'/>
            <input class='newznab_api' placeholder=' Api Key' type='text'/>
            <i class='newznab_clear fa fa-trash-o'/>
            <i class='indexer_test fa fa-plug', type='newznab'/>
        </li>
        `

        $("ul#newznab_list li:nth-last-child(2)").after(row);
    });

    $("div.providers i#add_torznab_row").click(function (){
        var row = `
        <li class='torznab_indexer'>
            <i class='fa fa-square-o torznab_check checkbox' value='False'/>
            <input class='torznab_url' placeholder=' http://indexer.url' type='text'/>
            <input class='torznab_api' placeholder=' Api Key' type='text'/>
            <i class='torznab_clear fa fa-trash-o'/>
            <i class='indexer_test fa fa-plug', type='torznab'/>
        </li>
        `

        $("div.providers ul#torznab_list li:nth-last-child(2)").after(row);
    });

    // clear row
    $("div.providers ul#newznab_list").on("click", "i.newznab_clear", function(){
        $(this).siblings("input").each(function(){
             $(this).val("");
        });
    });

    // test indexer connection
    $("div.providers").on("click", "i.indexer_test", function(){
        $this = $(this);

        $this.removeClass("fa-plug");
        $this.addClass("fa-circle faa-burst animated");
        var mode = $this.attr("type");
        var url = "";
        var api = "";

        $li = $this.parent();
        $li.find("input:eq(0)").each(function(){
            url = $(this).val();
        });

        $li.find("input:eq(1)").each(function(){
            api = $(this).val();
        });

        $.post(url_base + "/ajax/indexer_test", {"indexer": url, "apikey": api, "mode": mode})
        .done(function(r){
            response = JSON.parse(r);
            if(response["response"] == true){
                toastr.success(response["message"]);
            } else{
                toastr.error(response["message"])
            };


        $this.addClass("fa-plug");
        $this.removeClass("fa-circle faa-burst animated");

        })

    });


/* Downloader */

    // hide disabled download types
    $("div.downloader h2 i").click(function(){
        $this = $(this);
        tag = $this.attr("tag");
        if($this.attr("value") == "True"){
            $("ul#" + tag).slideUp();
        } else{
            $("ul#" + tag).slideDown();
        }
    });

    // set default state for radios and downloader options
    $("div.downloader i.radio").each(function(){
        $this = $(this);
        if ( $this.attr("value") == "True" ){
            u = ("ul#" + $this.attr("tog"));
            $(u).show()
            $this.removeClass("fa-circle-o")
            $this.addClass("fa-circle");
        }
    });

    // toggle downloader slide-downs
    $("div.downloader i.radio").click(function(){
        $this = $(this);
        var name = $this.attr("name");

        $downloaders = $this.parent().siblings()
        // turn on
        if( $this.attr("value") == "False" ){
            $this.attr("value", "True");
            $this.removeClass("fa-circle-o")
            $this.addClass("fa-circle");
        // and turn off the other ones
            var tog = $this.attr("tog");
            $("ul#"+tog).stop().slideDown();
            $downloaders.filter("ul").not("#"+tog).stop().slideUp()
            $("i.radio[name='" + name + "']").not($this).attr("value", "False").removeClass("fa-circle").addClass("fa-circle-o");
        }
    });

    // test downloader connection
    $("div.downloader span.test_connection").click(function(){
        $this = $(this)
        $thisi = $this.children(":first");

        $thisi.removeClass("fa-plug");
        $thisi.addClass("fa-circle faa-burst animated");

        var mode = $this.attr("mode");
        var inputs = "ul#" + mode + " li input";
        var checkboxes = "ul#" + mode + " li i.checkbox";

        // Gets entered info, even if not saved
        var data = {}
        $(inputs).each(function(){
            $this = $(this);
            if($this.attr('type') == 'number'){
                data[$this.attr('id')] = parseInt($this.val())
            } else {
                data[$this.attr('id')] = $this.val()
            }
        });

        $(checkboxes).each(function(){
            data[$(this).attr("id")] = $(this).attr("value")
        });

        data = JSON.stringify(data);

        $.post(url_base + "/ajax/test_downloader_connection", {
            "mode": mode,
            "data": data
        })
        .done(function(r){
            var response = JSON.parse(r);
            $thisi.addClass("fa-plug");
            $thisi.removeClass("fa-circle faa-burst animated");

            if(response["status"] == true){
                toastr.success(response["message"]);
            } else {
                toastr.error(response["error"]);
            }
        })
    });

/* Post-Processing */

    // Add new rows
    $("div.postprocessing ul#remote_mapping i#add_remote_mapping_row").click(function (){
        var row = `
        <li class='remote_mapping_row'>
            <span>Remote path: </span>
            <input class='remote_path' placeholder=' /home/user/downloads/watcher' type='text'/>
            <span>Local path: </span>
            <input class='local_path' placeholder=' //server/downloads/watcher' type='text'/>
            <i class='fa fa-trash-o mapping_clear'/>
        </li>
        `

        $("ul#remote_mapping li:nth-last-child(2)").after(row);
    });

    $("div.postprocessing ul#remote_mapping").on("click", "i.mapping_clear", function(){
        $(this).siblings("input").each(function(){
             $(this).val("");
        });
    });

/* Quality */

    // add new profile
    $("div.quality span#add_new_profile").click(function(){

        $("div#qualities").append(new_profile_html);

        $new_profile = $("div#qualities div.quality_profile").last();

        $new_sortable = $new_profile.find("ul.sortable")

        init_sortables($sortables=$new_sortable);

        $new_profile.slideDown();
    })


    // remove profile
    $("div.quality").on("click", "i.delete_profile", function(){
        $this = $(this);

        swal({
            title: "Delete quality profile?",
            text: "Any movies assigned to this profile will instead use Default until changed.",
            type: "",
            showCancelButton: true,
            confirmButtonColor: "#4CAF50",
            confirmButtonText: "Delete profile",
            closeOnConfirm: true
        }, function(){
            $profile = $this.parents("div.quality_profile");
            $profile.slideUp(500, function(){$(this).remove()})
        });
    })

/* Plugins */

    // apply plugin_conf overlay
    $("i.edit_conf").click(function(){
        $("div#overlay").fadeIn();
        $this = $(this);
        folder = $this.parents("ul").attr("id")
        conf = $this.attr("conf");
        $.post(url_base + "/ajax/get_plugin_conf", {"folder": folder, "conf": conf})
        .done(function(html){
            $("div#plugin_conf_popup").html(html).slideDown();
        });
    })

    $("body").on("click" ,"div#overlay", function(){
        $(this).fadeOut();
        $("div#plugin_conf_popup").slideUp();
        $("div#info_pop_up").empty();
    });


/* Logs */

    // Open log file
    $("span#view_log").click(function(){
        $log_display = $("pre#log_display");
        $log_display.hide();
        logfile = $("select#log_file").val();

        $.post(url_base + "/ajax/get_log_text", {"logfile": logfile})
        .done(function(r){
            $log_display.text(r);
            $log_display.show();
        });

    });

    // Download log file
    $("span#download_log").click(function(){
        logfile = $("select#log_file").val();
        window.open(url_base + "/logs/" + logfile)
    });

    var new_profile_html = `
    <div class="quality_profile hidden">
      <div class="name bold">
        <input class="name" type="text" value="New Profile"/>
      </div>
      <div class="sources">
        <span class="sub_heading">Sources</span>
        <ul class="sortable">
          <li id="BluRay-4K" sort="0">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="BluRay-4K" value="False"></i>
            <span>BluRay-4K</span>
          </li>
          <li id="BluRay-1080P" sort="1">
            <i class="fa fa-bars"></i>
            <i class="fa fa-check-square checkbox" id="BluRay-1080P" value="True"></i>
            <span>BluRay-1080P</span>
          </li>
          <li id="BluRay-720P" sort="2">
            <i class="fa fa-bars"></i>
            <i class="fa fa-check-square checkbox" id="BluRay-720P" value="True"></i>
            <span>BluRay-720P</span>
          </li>
          <li id="WebDL-4K" sort="3">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="WebDL-4K" value="False"></i>
            <span>WebDL-4K</span>
          </li>
          <li id="WebDL-1080P" sort="4">
            <i class="fa fa-bars"></i>
            <i class="fa fa-check-square checkbox" id="WebDL-1080P" value="True"></i>
            <span>WebDL-1080P</span>
          </li>
          <li id="WebDL-720P" sort="5">
            <i class="fa fa-bars"></i>
            <i class="fa fa-check-square checkbox" id="WebDL-720P" value="True"></i>
            <span>WebDL-720P</span>
          </li>
          <li id="WebRip-4K" sort="6">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="WebRip-4K" value="False"></i>
            <span>WebRip-4K</span>
          </li>
          <li id="WebRip-1080P" sort="7">
            <i class="fa fa-bars"></i>
            <i class="fa fa-check-square checkbox" id="WebRip-1080P" value="True"></i>
            <span>WebRip-1080P</span>
          </li>
          <li id="WebRip-720P" sort="8">
            <i class="fa fa-bars"></i>
            <i class="fa fa-check-square checkbox" id="WebRip-720P" value="True"></i>
            <span>WebRip-720P</span>
          </li>
          <li id="DVD-SD" sort="9">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="DVD-SD" value="False"></i>
            <span>DVD-SD</span>
          </li>
          <li id="Screener-1080P" sort="10">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="Screener-1080P" value="False"></i>
            <span>Screener-1080P</span>
          </li>
          <li id="Screener-720P" sort="11">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="Screener-720P" value="False"></i>
            <span>Screener-720P</span>
          </li>
          <li id="Telesync-SD" sort="12">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="Telesync-SD" value="False"></i>
            <span>Telesync-SD</span>
          </li>
          <li id="CAM-SD" sort="13">
            <i class="fa fa-bars"></i>
            <i class="fa fa-square-o checkbox" id="CAM-SD" value="False"></i>
            <span>CAM-SD</span>
          </li>
        </ul>
      </div>
      <div id="filters">
        <span class="sub_heading">Filters
          <span class="tip">Make groups with ampersands ( &amp; ) and split groups with commas ( , )</span>
        </span>
        <ul>
          <li class="bold">Required words:
            <span class="tip">Releases must contain one of these words or groups.</span>
          </li>
          <li>
            <input id="requiredwords" type="text" value="">
          </li>
          <li class="bold">Preferred words:
            <span class="tip">Releases with these words score higher.</span>
          </li>
          <li>
            <input id="preferredwords" type="text" value="">
          </li>
          <li class="bold">Ignored words:
            <span class="tip">Releases with these words are ignored.</span>
          </li>
          <li>
            <input id="ignoredwords" type="text" value="subs,german,dutch,french,truefrench,danish,swedish,spanish,italian,korean,dubbed,swesub,korsub,dksubs,vain,HC,blurred">
          </li>
        </ul>
      </div>
      <div id="toggles">
        <span class="sub_heading">Misc.</span>
        <ul>
          <li>
            <i class="fa fa-check-square checkbox" id="scoretitle" value="True"></i>
            <span>Score and filter titles.</span>
          </li>
          <li>
            <span class="tip">May need to disable for non-English results. Can cause incorrect downloads</span>
          </li>
          <li>
            <i class="fa fa-square-o checkbox" id="prefersmaller" value="False"></i>
            <span>Prefer smaller file sizes for identically-scored releases.</span>
          </li>
        </ul>
      </div>
      <i class='fa fa-trash delete_profile'/>
    </div>
    `


});

function init_sortables($sortables=false){
    if($sortables == false){
        var $sortables = $("ul.sortable")
    }

    $sortables.sortable({cancel: ".not_sortable"});
    $sortables.disableSelection();

    $sortables.each(function(){
        $this = $(this);

        $lis = $this.children("li").get();

        $lis.sort(function(a, b){
            var compa = parseInt($(a).attr("sort"));
            var compb = parseInt($(b).attr("sort"));
            return (compa < compb) ? -1 : (compa > compb) ? 1 : 0;
        })

        $.each($lis, function(idx, itm) {
                $this.append(itm);
            });
    })
}
