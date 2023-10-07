$(function() {
    var selector = '#usersuite-sidebar-nav';
    var $toc = $(selector);
    var $parent = $toc.parent();
    var offset = 60;
    var $body = $('body');
    Toc.init($toc);
    $body.scrollspy({
	target: selector,
	offset: offset
    });
    $toc.affix({
	offset: {
	    top: function() {
		return $parent.offset().top - offset;
	    }
	}
    });
    // Handle window resize
    $(window).resize(function(){
	$toc.affix('checkPosition');
    });
});
