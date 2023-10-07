function updateState() {
    var swdd_tenant = !$("#no_swdd_tenant").prop("checked");
    $("#tenant_number,[for=tenant_number]").toggle(swdd_tenant);
    $("#tenant_number").prop("required", swdd_tenant);

    var agdsn_history = $("#agdsn_history").prop("checked");
    $("#previous_dorm,[for=previous_dorm]").toggle(agdsn_history);
    $("#previous_dorm").prop("required", agdsn_history);
}
$("#no_swdd_tenant").change(updateState);
$("#agdsn_history").change(updateState);
updateState();
