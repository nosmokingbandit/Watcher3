jQuery.fn.justtext = function() {

	return $(this).clone()
			.children()
			.remove()
			.end()
			.text();
};

function read_cookie(){
   var dcookie = document.cookie;
   cookie_obj = {};
   cookiearray = dcookie.split("; ");

   // Now take key value pair out of this array
   for(var i=0; i<cookiearray.length; i++){
      key = cookiearray[i].split("=")[0];
      value = cookiearray[i].split("=")[1];
      cookie_obj[key] = value
   }
   return cookie_obj
}

function sortOrder(order, direction, $parent, children) {
	/*
	order : class with which to sort by
	direction: up or down for asc / desc
	parent : must be jquery object. Where to find children
	children : element of chilren to sort (li, span, etc)

	each child must have a span with class 'order'. text is taken from span to sort by.
	*/

	if(direction == "asc"){
		var forward = 1;
		var backward = -1;
	} else {
		var forward = -1;
		var backward = 1;
	}

	var	$element = $parent.children(children);

	$element.sort(function(a, b) {
		var an = $(a).find("span."+order).justtext(),
		bn = $(b).find("span."+order).justtext();

		if (an > bn)
			return forward;
		if (an < bn)
			return backward;

		return 0;
	});

	$element.detach().appendTo($parent);
}

var exp_date = new Date();
exp_date.setFullYear(exp_date.getFullYear() + 10);
exp_date = exp_date.toUTCString();

$(document).ready(function() {
    var url_base = $("meta[name='url_base']").attr("content");
    var $movielist = $("ul#movie_list");
	var cookie = read_cookie();

	/* set up list style and sort from cookies */
	style = cookie["list_style"] || "posters";
	direction = cookie["list_direction"] || "desc";
	order = cookie["list_sort"] || "title";

	$movielist.removeClass();
	$movielist.addClass(style);

	$("ul#list_style li").each(function(){
		$this = $(this);
		if($this.attr("id") == cookie["list_style"]){
			$this.addClass("selected")
		}
	});
	if(cookie["list_style"] == 'compact'){
		$('div#key').css('display', 'block');
	}

	sortOrder(order, direction, $movielist, "li");

	$("i#sort_direction").addClass("fa-sort-amount-" + direction);

	$("select#list_sort").find("option").each(function(){
		$this = $(this);
		if($this.val() == order){
			$this.prop("selected", true)
		}
	});

	/* Set cookies for list style and sort */
	$("ul#list_style li").click(function(){
		var $this = $(this);
		var $movielist = $("ul#movie_list")
        style = $this.attr('id');

		document.cookie = "list_style=" + style + "; expires=" + exp_date + ";path=/";

        $movielist.removeClass();
        $movielist.addClass(style);

		$("ul#list_style li").removeClass('selected');
		$this.addClass('selected');

		if(style == 'compact'){
			$('div#key').css('display', 'block');
		} else {
			$('div#key').css('display', 'none');
		}

    });

	$("i#sort_direction").click(function(){
		var $this = $(this);
		if($this.hasClass("fa-sort-amount-asc")){
			$this.removeClass("fa-sort-amount-asc");
			$this.addClass("fa-sort-amount-desc");
			direction = "desc";
			document.cookie = "list_direction=desc; expires=" + exp_date + ";path=/";

		} else {
			$this.removeClass("fa-sort-amount-desc");
			$this.addClass("fa-sort-amount-asc");
			direction = "asc";
			document.cookie = "list_direction=asc; expires=" + exp_date + ";path=/";
		}

		sortOrder(order, direction, $('ul#movie_list'), "li")
	});

    $("select#list_sort").change(function(){
        order = $(this).find("option:selected").val()

		document.cookie = "list_sort=" + order + ";path=/";

        sortOrder(order, direction, $('ul#movie_list'), "li")

    });

    /* applies add movie overlay */
    $("div#content").on("click", "ul#movie_list li", function(){
        $("div#overlay").fadeIn();
        imdbid = $(this).attr("imdbid");

        $.post(url_base + "/ajax/movie_status_popup", {"imdbid": imdbid})
            .done(function(html){
                $("div#status_pop_up").html(html);
                $("div#status_pop_up").slideDown();
            });
    });

    $("body").on("click" ,"div#overlay", function(){
        $(this).fadeOut();
        $("div#status_pop_up").slideUp();
        $("div#status_pop_up").empty();

    });


});
