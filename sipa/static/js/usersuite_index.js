document.addEventListener("DOMContentLoaded", () => {
    const selector = '#usersuite-sidebar-nav';
    const $toc = $(selector);
    const $parent = $toc.parent();
    const offset = 60;
    const $body = $('body');
    Toc.init($toc);
    $body.scrollspy({target: selector, offset: offset});
    $toc.affix({
        offset: {top: () => $parent.offset().top - offset}
    });
    // Handle window resize
    $(window).resize(() => $toc.affix('checkPosition'));
});
