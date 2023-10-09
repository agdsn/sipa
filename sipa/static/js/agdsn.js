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
 * @typedef {"fullOutage" | "maintenance" | "partialOutage" | "performanceIssues" | "okay"} StatusCode
 */
/**
 * @param {Array<Status>} statuses
 * @returns {StatusCode}
 */
function determineStatus(statuses) {
    if (statuses.some(s => s === 'major_outage')) {
        return "fullOutage";
    }
    if (statuses.some(s => s === "partial_outage")) {
        return "partialOutage";
    }
    if (statuses.some(s => s === "maintenance")) {
        return "maintenance";
    }
    if (statuses.some(s => s === "degraded_performance")) {
        return "performanceIssues";
    }
    return "okay";
}

/**
 * Applies the status of the components to the status widget
 * @param {Array<Component>} components – the component information
 */
function initStatus(components) {
    const statusCode = determineStatus(
        [...components.map(c => c.status)]
    );

    let status = $('.services-status'),
        icon = $('.services-status .glyphicon'),
        link = $('.services-status a');

    icon.removeClass('glyphicon-question-sign')
        .addClass(statusMessages[statusCode]['classes']);
    link.html(statusMessages[statusCode][get_language()]);

    if (statusCode !== "okay") {
        let issueDescriptions = components
            .filter(c => c.status !== 'operational')
            .map(c => $`<div>${(status_to_icon(c.status))} ${c.name}</div>`)
            .join("");

        status.data('content', issueDescriptions)
            .popover({trigger: 'hover focus', html: true, placement: 'bottom'});
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Statuspage('https://status.agdsn.net/pubapi/services/all', initStatus);
});
