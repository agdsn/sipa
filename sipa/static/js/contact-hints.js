let hints = [];

fetch("static/js/hints.json").then(response => response.json()).then((raw_hints) => {
    hints = raw_hints.map((hint) => {
        return {
            not_in_dorm: hint.not_in_dorm,
            patterns: hint.patterns.map((pattern) => {
                return new RegExp(pattern, "i");
            }),
            hint: hint.hint
        };
    });
});


const e_message = document.getElementById("message");
const e_dormitory = document.getElementById("dormitory");
const e_hints = document.getElementById("hints")

e_message.addEventListener("input", (event) => {
    const applicable = hints.filter((hint) => {
        const contains = hint.patterns.some((pattern) => {
            return pattern.test(e_message.value)
        });
        const not_blacklisted = hint.not_in_dorm.every((dorm) => {
            return dorm !== e_dormitory.value;
        });
        return contains & not_blacklisted;
    });

    while (e_hints.lastChild) {
        e_hints.removeChild(e_hints.lastChild);
    }
    applicable.forEach((hint) => {
        e_hints.insertAdjacentHTML("beforeend",
            "<div class='alert alert-warning'>" + hint.hint[get_language()] +
            "</div>"
        );
    });
});
