(function () {
    let CachetStatus = function (url, callback) {
        this.init(url, callback);
    };

    CachetStatus.DEFAULTS = {
        endpointPath: '/api/v1/components?per_page=100'
    };

    CachetStatus.prototype.init = function (url, callback) {
        this.url = url.concat(CachetStatus.DEFAULTS.endpointPath);
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
                        status: data[i].status_name.toLowerCase(),
                        group_id: data[i].group_id,
                    });
                }

                components.sort(function (f, s) {
                    if (f.name > s.name) {
                        return 1;
                    } else if (f.name < s.name) {
                        return -1;
                    } else {
                        return 0;
                    }
                });

                components.sort(function (f, s) {
                    if (f.group_id > s.group_id) {
                        return 1;
                    } else if (f.group_id < s.group_id) {
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
            if (sessionStorage.cachetCacheExpires && parseInt(sessionStorage.cachetCacheExpires) > Date.now()
                && sessionStorage.cachetCache !== null && sessionStorage.cachetCache[this.url] !== null) {

                let response = JSON.parse(sessionStorage.cachetCache)[this.url];

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
                if (typeof (sessionStorage.cachetCache) !== 'string') {
                    sessionStorage.cachetCache = '{}';
                }

                let cache = JSON.parse(sessionStorage.cachetCache);

                cache[this.url] = response;

                sessionStorage.cachetCache = JSON.stringify(cache);
                sessionStorage.cachetCacheExpires = Date.now() + (120 * 1000)
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

    window.CachetStatus = CachetStatus;
})();
