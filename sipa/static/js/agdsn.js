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
/**
 * @param {Status} status
 * @returns {string} HTML for the icon
 */
function status_to_icon(status) {
    switch (status) {
        case 'degraded_performance':
            return '<span class="glyphicon glyphicon-exclamation-sign text-primary"></span>';
        case 'maintenance':
            return '<span class="glyphicon glyphicon-info-sign text-primary"></span>';
        case 'partial_outage':
            return '<span class="glyphicon glyphicon-exclamation-sign text-warning"></span>';
        case 'major_outage':
            return '<span class="glyphicon glyphicon-exclamation-sign text-danger"></span>';
        default:
            return "";
    }
}
/**
 * Applies the status of the components to the status widget
 * @param {Array<Component>} components – the component information
 */
function initStatus (components) {
    let content = '';
    let statusCode = 'okay';
    let allGood = true;

    for (const component of components) {
        /** whether to list this component.
         *
         * true whenever status is not operational,
         * and in that case, $`<div> {icon} {component.name}</div>` is emitted.*/
        let listComponent = false;

        if (component.status === 'degraded_performance') {
            if(statusCode === 'okay') {
                statusCode = 'performanceIssues';
            }
            listComponent = true
        } else if (component.status === 'maintenance') {
            if(statusCode === 'okay'){
                statusCode = 'maintenance';
            }
            listComponent = true
        } else if (component.status === 'partial_outage') {
            if(statusCode === 'okay' || statusCode === 'performanceIssues'){
                statusCode = 'partialOutage';
            }
            listComponent = true
        }else if (component.status === 'major_outage') {
            statusCode = 'fullOutage';
            listComponent = true
        }

        if (listComponent){
            content += $`<div>${(status_to_icon(component.status))} ${component.name}</div>`
        }

        if (component.status !== 'operational') {
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
}

document.addEventListener('DOMContentLoaded', () => {
    new Statuspage('https://status.agdsn.net', initStatus);
});
