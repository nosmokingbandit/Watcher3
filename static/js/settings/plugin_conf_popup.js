$(document).ready(function() {
    var url_base = $("meta[name='url_base']").attr("content");

    $('i#close').click(function(e) {
        $('div#overlay').fadeOut();
        $('div#plugin_conf_popup').slideUp();
        $("div#plugin_conf_popup").empty();
        e.preventDefault();
    });

    $('i#save_plugin_conf').click(function(e){
        $this = $(this);
        $this.removeClass('fa-save');
        $this.addClass('fa-circle faa-burst animated');

        $ul = $("ul#plugin_conf")

        conf = $ul.attr("conf");
        folder = $ul.attr("folder")

        data = {}
        $ul.find("li input").each(function(){
            $input = $(this);
            key = $input.attr("id");
            value = $input.val();
            data[key] = value;
        })

        data = JSON.stringify(data);

        $.post(url_base + "/ajax/save_plugin_conf", {"folder": folder, "conf": conf, "data": data})
        .done(function(r){
            response = JSON.parse(r)

            if(response['response'] == true){
                toastr.success(response['message']);
            } else {
                toastr.error(response['error']);
            };
            $this.addClass('fa-save');
            $this.removeClass('fa-circle faa-burst animated');
        });

    e.preventDefault();
    })
});
