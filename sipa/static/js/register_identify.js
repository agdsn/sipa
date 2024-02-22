function updateForm(target, invert, updateId, event) {
    // Invert checked if invert is true (XOR)
    const shouldBeVisible = target.checked !== invert;

    const element = document.getElementById(updateId);
    element.style.display = shouldBeVisible ? "block" : "none";
    element.required = shouldBeVisible;

    element.labels.forEach((label) => {
        label.style.display = shouldBeVisible ? "block" : "none";
    });
}

const no_swdd_tenant = document.getElementById("no_swdd_tenant");
no_swdd_tenant.addEventListener("change", updateForm.bind(undefined, no_swdd_tenant, true, "tenant_number"));

const agdsn_history = document.getElementById("agdsn_history");
agdsn_history.addEventListener("change", updateForm.bind(undefined, agdsn_history, false, "previous_dorm"));

updateForm(no_swdd_tenant, true, "tenant_number", undefined)
updateForm(agdsn_history, false, "previous_dorm", undefined)
