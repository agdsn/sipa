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

const noSwddTenant = document.getElementById("no_swdd_tenant");
noSwddTenant.addEventListener("change", updateForm.bind(undefined, noSwddTenant, true, "tenant_number"));

const agdsnHistory = document.getElementById("agdsn_history");
agdsnHistory.addEventListener("change", updateForm.bind(undefined, agdsnHistory, false, "previous_dorm"));

updateForm(noSwddTenant, true, "tenant_number", undefined)
updateForm(agdsnHistory, false, "previous_dorm", undefined)
