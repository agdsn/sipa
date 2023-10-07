$("#dorm-select").change(function(){
    selected = $("select#dorm-select").find(":selected").prop("value");
    $(".dynamic-content").hide();
    $("#dynamic-" + selected).show();
});
$("#dorm-select").on("load", function() {}).triggerHandler("change")
