function get_language() {
    return JSON.parse(document.getElementById('locale').innerHTML);
}

let statusMessages = {
    'okay': {
        'de': 'Derzeit sind keine Probleme bekannt.',
        'en': 'There are currently no known issues.',
        'classes': 'glyphicon-ok-sign text-success',
    },
    'partialOutage': {
        'de': 'Es gibt derzeit einen teilweisen Ausfall.',
        'en': 'There is currently a partial outage.',
        'classes': 'glyphicon-exclamation-sign text-warning',
    },
    'fullOutage':{
        'de': 'Es gibt derzeit einen schweren Ausfall',
        'en': 'There is currently a critical outage.',
        'classes': 'glyphicon-exclamation-sign text-danger',
    }
}

//Status widget
var initStatus = function (components) {
    var content = '',
        statusCode = 'okay';

    for (var i = 0; i < components.length; i++) {
        content += '<div>';
        if (components[i].status === 'funktionsfähig') {
            content += '<span class="glyphicon glyphicon-ok-sign text-success"></span>';
        } else if (components[i].status === 'teilweiser ausfall' || components[i].status === 'leistungsprobleme') {
            content += '<span class="glyphicon glyphicon-exclamation-sign text-warning"></span>';

            if(statusCode === 'okay'){
                statusCode = 'partialOutage';
            }
        } else {
            content += '<span class="glyphicon glyphicon-exclamation-sign text-danger"></span>';
            statusCode = 'fullOutage';
        }
        content += ' ' + components[i].name;
        content += '</div>';

        if (components[i].status !== 'operational') {
            allGood = false;
        }
    }

    let status = $('.services-status'),
        icon = $('.services-status .glyphicon'),
        link = $('.services-status a');

    icon.removeClass('glyphicon-question-sign')
            .addClass(statusMessages[statusCode]['classes']);

    link.html(statusMessages[statusCode][get_language()]);

    // Set content of the popover window and activate it
    status.data('content', content)
        .popover({trigger: 'hover focus', html: true, placement: 'bottom'});
};

new CachetStatus('https://status.agdsn.net', initStatus);
