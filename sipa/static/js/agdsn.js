function get_language() {
    return JSON.parse(document.getElementById('locale').innerHTML);
}

if (window.location.pathname.endsWith("contact")) {
    var hints = [];
    $.getJSON("static/js/hints.json", function (raw_hints) {
        hints = raw_hints.map(function (hint) {
            return {
                not_in_dorm: hint.not_in_dorm,
                patterns: hint.patterns.map(function (pattern) {
                    return new RegExp(pattern, "i");
                }),
                hint: hint.hint
            };
        });
    });
    $("#message").keypress(function () {
        var applicable = hints.filter(function (hint) {
            var contains = hint.patterns.some(function (pattern) {
                return pattern.test($("#message").val())
            });
            var not_blacklisted = hint.not_in_dorm.every(function (dorm) {
                return dorm !== $("#dormitory").val();
            });
            return contains & not_blacklisted;
        });
        $("#hints").empty();
        applicable.forEach(function (hint) {
            var hint_text = hint.hint[get_language()];
            $("#hints").append("<div class='alert alert-warning'>" + hint_text + "</div>");
        });
    });
}