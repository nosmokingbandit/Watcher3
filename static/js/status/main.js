jQuery.fn.justtext = function() {

	return $(this)	.clone()
			.children()
			.remove()
			.end()
			.text();
};

function read_cookie()
{
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
function sortOrder(order, $parent, children) {
	/* order : how to sort children
	parent : must be jquery object. Where to find children
	children : element of chilren to sort (li, span, etc)

	each child must have a span with class 'order'. text is taken from span to sort by.
	*/

		$element = $parent.children(children);

	$element.sort(function(a, b) {
		var an = $(a).find("span."+order).justtext(),
		bn = $(b).find("span."+order).justtext();

		if (an > bn)
			return 1;
		if (an < bn)
			return -1;

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
	$movielist.removeClass();
	$movielist.addClass(style);

	$("select#list_style").find("option").each(function(){
		$this = $(this);
		if($this.val() == cookie["list_style"]){
			$this.prop("selected", true);
		}
		if(cookie["list_style"] == 'compact'){
			$('div#key').css('display', 'block');
		}
	});

	order = cookie["list_sort"] || "title";
	sortOrder(order, $movielist, "li");

	$("select#list_sort").find("option").each(function(){
		$this = $(this);
		if($this.val() == order){
			$this.prop("selected", true)
		}
	});

    /* applies add movie overlay */
    $("div#content").on("click", "li", function(){
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

	/* Set cookies for list style and sort */
    $("select#list_style").change(function(){
		var $movielist = $("ul#movie_list")
        style = $("select#list_style").find("option:selected").val()

		document.cookie = "list_style=" + style + "; expires=" + exp_date + ";path=/";

        $movielist.removeClass();
        $movielist.addClass(style);

		if(style == 'compact'){
			$('div#key').css('display', 'block');
		} else {
			$('div#key').css('display', 'none');
		}

    });

    $("select#list_sort").change(function(){
        order = $(this).find("option:selected").val()

		document.cookie = "list_sort=" + order + ";path=/";

        sortOrder(order, $('ul#movie_list'), "li")

    });


});
