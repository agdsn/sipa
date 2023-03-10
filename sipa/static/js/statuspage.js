/** Extract components (services) from statuspage API response sorted by priority
 *
 * @param data the JSON response from `/services/all`
 * @returns Array
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
    static DEFAULTS = {endpointPath: '/pubapi/services/all'};

    constructor(url, callback) {
        this.url = url.concat(Statuspage.DEFAULTS.endpointPath);
        this.callback = callback || function () {
        };

        let self = this;
        new Request(
            this.url,
            data => self.callback.call(null, parse_statuspage_data(data)),
            err => {
                throw new Error(err);
            },
        );
    }
}

class Request {
    constructor(url, success, error) {
        this.url = url;
        this.success = success;
        this.error = error;
        this.async = true;

        const cached = getResponseCache(this.url);
        if (cached !== null) {
            this.success.call(null, cached);
            return;
        }

        let self = this;
        let xhr = typeof XMLHttpRequest != undefined
            ? new XMLHttpRequest()
            : new ActiveXObject('Microsoft.XMLHTTP');

        xhr.onload = function (event) {
            self.onLoad.call(self, event);
        }
        xhr.onerror = function (event) {
            self.onError.call(self, event);
        }

        xhr.open('get', this.url, this.async);
        xhr.send();
    }

    onLoad(event) {
        let xhr = event.currentTarget,
            response = JSON.parse(xhr.response);

        if (xhr.status === 200) {
            setResponseCache(this.url, response, CACHE_RETENTION_MS);
            this.success.call(null, response);
        } else {
            this.error.call(null, response);
        }
    }

    onError(event) {
        let xhr = event.currentTarget,
            response = JSON.parse(xhr.response);

        this.error.call(null, response);
    }

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
    if (!cache.hasOwnProperty(url)) {
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
