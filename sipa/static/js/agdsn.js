function guess_locale() {
    // the locale defined in a cookie takes precedence
    if (document.cookie.includes("de")) {
        return "de"
    }
    if (document.cookie.includes("en")) {
        return "en"
    }

    // if no cookie is found use the browsers default or english if the default language is not supported
    if (navigator.language.toLowerCase().includes("de")) {
        return "de";
    }
    return "en";
}

if (window.location.pathname.endsWith("contact")) {
    var hints = [];
    $.getJSON("static/js/hints.json", function (raw_hints) {
        hints = raw_hints.map(function (hint) {
            return {
                not_in: hint.not_in,
                patterns: hint.patterns.map(function (pattern) {
                    return new RegExp(pattern, "i");
                }),
                hint_de: hint.hint_de,
                hint_en: hint.hint_en
            };
        });
    });
    $("#message").keypress(function () {
        var applicable = hints.filter(function (hint) {
            var contains = hint.patterns.some(function (pattern) {
                return pattern.test($("#message").val())
            });
            var not_blacklisted = hint.not_in.every(function (dorm) {
                return dorm !== $("#dormitory").val();
            });
            return contains & not_blacklisted;
        });
        $("#hints").empty();
        applicable.forEach(function (hint) {
            var hint_text = guess_locale() === "de" ? hint.hint_de : hint.hint_en;
            $("#hints").append("<div class='alert alert-warning'>" + hint_text + "</div>");
        });
    });
}