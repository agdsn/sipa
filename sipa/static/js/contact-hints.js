let hints = [];

fetch("static/js/hints.json").then(response => response.json()).then((rawHints) => {
    hints = rawHints.map(({
        not_in_dorm,
        patterns,
        hint
    }) => ({
        not_in_dorm,
        patterns: patterns.map((pattern) => new RegExp(pattern, "i")),
        hint
    }));
});


const eMessage = document.getElementById("message");
const eDormitory = document.getElementById("dormitory");
const eHints = document.getElementById("hints");

const lang = get_language();

eMessage.addEventListener("input", (event) => {
    const applicable = hints.filter((hint) => {
        const contains = hint.patterns.some(
            (pattern) => pattern.test(eMessage.value)
        );
        const not_blacklisted = hint.not_in_dorm.every(
            (dorm) => dorm !== eDormitory.value
        );
        return contains & not_blacklisted;
    });

    while (eHints.lastChild) {
        eHints.removeChild(eHints.lastChild);
    }
    applicable.forEach((hint) => {
        eHints.insertAdjacentHTML("beforeend",
            `<div class='alert alert-warning'>${hint.hint[lang]}</div>`
        );
    });
});
