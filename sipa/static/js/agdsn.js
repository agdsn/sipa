function get_language() {
    return JSON.parse(document.getElementById('locale').innerHTML);
}

let statusMessages = {
    'okay': {
        'de': 'Derzeit sind keine Probleme bekannt.',
        'en': 'There are currently no known issues.',
        'classes': 'glyphicon-ok-sign text-success',
    },
    'maintenance': {
        'de': 'Derzeit findet eine Wartung statt.',
        'en': 'There is an ongoing maintenance.',
        'classes': 'glyphicon-info-sign text-primary',
    },
    'performanceIssues': {
        'de': 'Es gibt derzeit Leistungsprobleme.',
        'en': 'There are currently performance issues.',
        'classes': 'glyphicon-exclamation-sign text-primary',
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
    let content = '',
        statusCode = 'okay'
        allGood = true;

    for (var i = 0; i < components.length; i++) {
        let listComponent = false;
        let new_content = '<div>';

        if (components[i].status === 'degraded_performance') {
            new_content += '<span class="glyphicon glyphicon-exclamation-sign text-primary"></span>';

            if(statusCode === 'okay') {
                statusCode = 'performanceIssues';
            }

            listComponent = true
        } else if (components[i].status === 'maintenance') {
            new_content += '<span class="glyphicon glyphicon-info-sign text-primary"></span>';

            if(statusCode === 'okay'){
                statusCode = 'maintenance';
            }

            listComponent = true
        } else if (components[i].status === 'partial_outage') {
            new_content += '<span class="glyphicon glyphicon-exclamation-sign text-warning"></span>';

            if(statusCode === 'okay' || statusCode === 'performanceIssues'){
                statusCode = 'partialOutage';
            }

            listComponent = true
        }else if (components[i].status === 'major_outage') {
            new_content += '<span class="glyphicon glyphicon-exclamation-sign text-danger"></span>';

            statusCode = 'fullOutage';

            listComponent = true
        }

        new_content += ' ' + components[i].name;
        new_content += '</div>';

        if (listComponent){
            content += new_content
        }

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
    if(!allGood){
        status.data('content', content)
        .popover({trigger: 'hover focus', html: true, placement: 'bottom'});
    }
};

new Statuspage('https://status.agdsn.net', initStatus);
