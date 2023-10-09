/**
 * @typedef {'degraded_performance' | 'maintenance' | 'partial_outage' | 'major_outage' | 'operational'} Status
 * @typedef {{ status: Status, name: string }} Component
 * */

/** Extract components (services) from statuspage API response sorted by priority
 *
 * @param {object} data the JSON response from the API endpoint
 * @returns Array<Component>
 */
function parse_statuspage_data(data) {
    let {results} = data;
    if (results === undefined) {
        throw new Error('Invalid statuspage response (`results` key missing)');
    }

    let components = Array.from(results.map((comp) => ({
        name: comp.name,
        status: comp.status.toLowerCase(),
        order: comp.order,
    })));
    components.sort((f, s) => f.order - s.order);
    return components;
}

class Statuspage {
    constructor(url, callback) {
        this.url = url;
        this.callback = callback || function () {
        };

        let self = this;
        issueCachedRequest(
            this.url,
            data => self.callback.call(null, parse_statuspage_data(data)),
            err => {
                throw new Error(err);
            },
        );
    }
}

function issueCachedRequest(url, onSuccess, onError) {
    const cached = getResponseCache(url);
    if (cached !== null) {
        onSuccess(cached);
        return;
    }

    fetch(url)
        .then(r => r.ok ? Promise.resolve(r) : Promise.reject(r))
        .then(r => r.json())
        .then(d => {
            setResponseCache(url, d, CACHE_RETENTION_MS);
            onSuccess(d);
        })
        // NOTE: this catches all the possible errors in the above pipeline:
        // network, json parsing, etc.;
        // so `e` can be either a response or a network error etc.
        .catch(e => onError.call(null, e));
}


/** Return a (non-expired) cached response object for the desired url, or `null`.
 *
 * @param url
 * @returns {null|*}
 */
function getResponseCache(url) {
    const expires = sessionStorage.statuspageCacheExpires;
    if (expires === undefined || expires < Date.now()) {
        return null;
    }
    const content = sessionStorage.statuspageCache;
    if (content === undefined) {
        console.warn('Corrupt cache: statuspageCacheExpires is set, but statuspageCache is not');
        return null;
    }
    const cache = JSON.parse(sessionStorage.statuspageCache);
    if (cache[url] === undefined) {
        console.debug(`Cache miss for ${url}`)
        return null;
    }
    console.debug(`Cache hit for ${url}`);
    return cache[url]
}


function setResponseCache(url, response, retention_ms) {
    if (typeof (sessionStorage.statuspageCache) !== 'string') {
        sessionStorage.statuspageCache = '{}';

    }
    let cache = JSON.parse(sessionStorage.statuspageCache);
    cache[url] = response;
    sessionStorage.statuspageCache = JSON.stringify(cache);
    sessionStorage.statuspageCacheExpires = Date.now() + retention_ms
}

const CACHE_RETENTION_MS = 120 * 1000;

window.Statuspage = Statuspage;
