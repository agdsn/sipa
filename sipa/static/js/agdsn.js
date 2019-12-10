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
    $("#message").on("input", function () {
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

//Status widget
var initStatus = function (components) {
  var content = '',
    partialOutage = false,
    fullOutage = false;

  for (var i = 0; i < components.length; i++) {
    content += '<div>';
    if (components[i].status === 'funktionsfähig') {
      content += '<span class="glyphicon glyphicon-ok-sign text-success"></span>';
    } else if (components[i].status === 'teilweiser ausfall' || components[i].status === 'leistungsprobleme') {
      content += '<span class="glyphicon glyphicon-exclamation-sign text-warning"></span>';
      partialOutage = true;
    } else {
      content += '<span class="glyphicon glyphicon-exclamation-sign text-danger"></span>';
      fullOutage = true;
    }
    content += ' ' + components[i].name;
    content += '</div>';

    if (components[i].status !== 'operational') {
      allGood = false;
    }
  }

  let status = $('#services-status'),
      icon = $('#services-status .glyphicon'),
      link = $('#services-status a');

  if (fullOutage){
      icon.removeClass('glyphicon-question-sign')
      .addClass('glyphicon-exclamation-sign text-danger');

      link.html("Es gibt derzeit einen schweren Ausfall");
  }else if(partialOutage){
      icon.removeClass('glyphicon-question-sign')
      .addClass('glyphicon-exclamation-sign text-warning');

      link.html("Es gibt derzeit einen teilweisen Ausfall");
  }else{
      icon.removeClass('glyphicon-question-sign')
      .addClass('glyphicon-ok-sign text-success');
      link.html("Derzeit sind alle Systeme funktionsfähig");
  }

  // Set content of the popover window and activate it
  status.data('content', content)
        .popover({ trigger: 'hover focus', html: true, placement: 'bottom' });
};

new CachetStatus('https://status.agdsn.net', initStatus);
