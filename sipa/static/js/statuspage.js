(function () {
    let Statuspage = function (url, callback) {
        this.init(url, callback);
    };

    Statuspage.DEFAULTS = {
        endpointPath: '/pubapi/services/all'
    };

    Statuspage.prototype.init = function (url, callback) {
        this.url = url.concat(Statuspage.DEFAULTS.endpointPath);
        this.callback = callback || function () {
        };

        let self = this;

        new Request(
            this.url,
            function (response) {
                let data = response.data,
                    components = [];

                for (let i = 0; i < data.length; i++) {
                    components.push({
                        name: data[i].name,
                        status: data[i].status.toLowerCase(),
                        order: data[i].order,
                    });
                }

                components.sort(function (f, s) {
                    if (f.order > s.order) {
                        return 1;
                    } else if (f.order < s.order) {
                        return -1;
                    } else {
                        return 0;
                    }
                });

                self.callback.call(null, components);
            },
            function (response) {
                throw new Error(response);
            }
        );
    };

    let Request = function (url, success, error) {
        this.init(url, success, error);
    };

    Request.prototype.init = function (url, success, error) {
        this.url = url;
        this.success = success;
        this.error = error;
        this.async = true;

        if (typeof (Storage) !== "undefined") {
            if (sessionStorage.statuspageCacheExpires && parseInt(sessionStorage.statuspageCacheExpires) > Date.now()
                && sessionStorage.statuspageCache !== null && sessionStorage.statuspageCache[this.url] !== null) {

                let response = JSON.parse(sessionStorage.statuspageCache)[this.url];

                if (response) {
                    this.success.call(null, response);

                    return
                }
            }
        }

        let self = this;
        xhr = typeof XMLHttpRequest != undefined
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
    };

    Request.prototype.onLoad = function (event) {
        let xhr = event.currentTarget,
            response = JSON.parse(xhr.response);

        if (xhr.status === 200) {
            if (typeof (Storage) !== "undefined") {
                if (typeof (sessionStorage.statuspageCache) !== 'string') {
                    sessionStorage.statuspageCache = '{}';
                }

                let cache = JSON.parse(sessionStorage.statuspageCache);

                cache[this.url] = response;

                sessionStorage.statuspageCache = JSON.stringify(cache);
                sessionStorage.statuspageCacheExpires = Date.now() + (120 * 1000)
            }

            this.success.call(null, response);
        } else {
            this.error.call(null, response);
        }
    };

    Request.prototype.onError = function (event) {
        let xhr = event.currentTarget,
            response = JSON.parse(xhr.response);

        this.error.call(null, response);
    };

    window.Statuspage = Statuspage;
})();
