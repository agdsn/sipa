function get_language() {
    return JSON.parse(document.getElementById('locale').innerHTML);
}

/**
 * @typedef {{de: string, classes: string, en: string}} StatusMessage
 */
/**
 * @type {Record<StatusCode, StatusMessage>}
 */
const statusMessages = {
    'okay': {
        'de': 'Derzeit sind keine Probleme bekannt.',
        'en': 'There are currently no known issues.',
        'classes': 'bi-check-circle-fill text-success',
    },
    'maintenance': {
        'de': 'Derzeit findet eine Wartung statt.',
        'en': 'There is an ongoing maintenance.',
        'classes': 'bi-info-circle-fill text-primary',
    },
    'performanceIssues': {
        'de': 'Es gibt derzeit Leistungsprobleme.',
        'en': 'There are currently performance issues.',
        'classes': 'bi-exclamation-circle-fill text-primary',
    },
    'partialOutage': {
        'de': 'Es gibt derzeit einen teilweisen Ausfall.',
        'en': 'There is currently a partial outage.',
        'classes': 'bi-exclamation-circle-fill text-warning',
    },
    'fullOutage':{
        'de': 'Es gibt derzeit einen schweren Ausfall',
        'en': 'There is currently a critical outage.',
        'classes': 'bi-exclamation-circle-fill text-danger',
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
            return '<span class="bi-exclamation-circle-fill text-primary"></span>';
        case 'maintenance':
            return '<span class="bi-info-circle-fill text-primary"></span>';
        case 'partial_outage':
            return '<span class="bi-exclamation-circle-fill text-warning"></span>';
        case 'major_outage':
            return '<span class="bi-exclamation-circle-fill text-danger"></span>';
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
        icon = $('.services-status .service_status'),
        link = $('.services-status a');

    icon.removeClass('bi-question-circle-fill')
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
