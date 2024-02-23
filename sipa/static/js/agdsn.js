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

const maintenanceMessage = {
    'de': 'Es stehen Wartungen an!',
    'en': 'Upcomming maintenances!'
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
 * @param {StatusMessage} statusMessage
 * @param {HTMLElement} statusEl
 * @param {?string} tooltipContent
 */
function updateStatusWidget(statusMessage, statusEl, tooltipContent) {
    // icon
    for (const icon of statusEl.getElementsByClassName("service_status")) {
        icon.classList.remove('bi-question-circle-fill');
        icon.classList.add(...statusMessage.classes.split(" "));
    }
    // link
    for (const link of statusEl.getElementsByTagName("a")) {
        link.classList.remove("placeholder");
        link.innerHTML = statusMessage[get_language()];
        // tooltip
        if (tooltipContent) {
            link.dataset.bsTitle = tooltipContent;
            new bootstrap.Tooltip(link);
        }
    }
}

/**
 * @param {HTMLElement} statusEl
 * @param {?string} tooltipContent
 */
function updateMaintenancesPartOfStatusWidget(statusEl, tooltipContent) {
    if (tooltipContent) {
        for (const link of statusEl.getElementsByTagName("a")) {
            const parent = link.parentElement;
            if (parent.tagName.toLowerCase() == "div") {
                parent.innerHTML += `<br><span class="bi-clock-fill text-muted"></span>`
                const spanElement = document.createElement("span");
                spanElement.innerHTML += ` ${maintenanceMessage[get_language()]}`;
                spanElement.classList.add(...'text-decoration-none text-muted'.split(" "));
                spanElement.setAttribute("data-bs-toggle", "tooltip");
                spanElement.setAttribute("data-bs-placement", "bottom");
                spanElement.setAttribute("data-bs-html", "true");
                parent.append(spanElement);
                spanElement.dataset.bsTitle = tooltipContent;
                new bootstrap.Tooltip(spanElement);
            }
        }
    }
}

/**
 * Applies the status of the components to the status widget
 * @param {Array<Component>} components – the component information
 */
function handleStatusResponse(components) {
    const statusCode = determineStatus(
        [...components.map(c => c.status)]
    );
    const statusMessage = statusMessages[statusCode]
    const issueDescriptions =
        statusCode === null ? "" : components
            .filter(c => c.status !== 'operational')
            .map(c => `<div>${(status_to_icon(c.status))} ${c.name}</div>`)
            .join("");

    for (const statusEl of document.getElementsByClassName("services-status")) {
        updateStatusWidget(statusMessage, statusEl, issueDescriptions);
    }
}

/**
 * Applies upcomming maintenances to the status widget
 * @param {Array<Maintenance>} maintenances – the maintenance information
 */
function handleMaintenancesResponse(maintenances) {
    const issueDescriptions = maintenances
        .filter(m => m.status == 'schedule')
        .map(m => `<div><span class="bi-info-circle-fill text-primary"></span> ${m.title}</div>`)
        .join("");
    for (const statusEl of document.getElementsByClassName("services-status")) {
        updateMaintenancesPartOfStatusWidget(statusEl, issueDescriptions);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Statuspage(
        'https://status.agdsn.net/pubapi/services/all',
        // replace URL by this for testing
        // "/static/statuspage.json",
        handleStatusResponse,
        'https://status.agdsn.net/pubapi/maintenances/all',
        handleMaintenancesResponse
    );
});
