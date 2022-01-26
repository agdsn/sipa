'use strict';

L.NetworkLayer = (L.Layer ? L.Layer : L.Class).extend({

	/*------------------------------------ LEAFLET CONFIG ------------------------------------------*/

	options: {
		allColor: 'purple',
		arrows: true,
		arrowSpacing: 100,
		clipRange: null,
		colorScale: ['#7EC891', '#FE5E69'],
		data: [],
		displayMode: 'ANY',
		displayInactive: true,
		globalScaleDomain: null,
		lineDashStyle: null,
		lineInactiveColor: 'grey',
		lineInactiveOpacity: 0.2,
		lineOpacity: 0.8,
		lineWidth: 2,
		lineWidthActive: 2,
		nodeFillColor: 'red',
		nodeOpacity: 0.5,
		nodeRadius: 5,
		onClickNode: null,
		onMouseEnterNode: null,
		onMouseLeaveNode: null,
		onMouseEnterLine: null,
		onMouseLeaveLine: null,
		sinkColor: '#7EC891',
		sourceColor: '#FE5E69',
		weightMode: 'NONE'
	},

	_active: false,
	_map: null,
	_mapSvg: null, // our root SVG layer
	_svgGroup1: null,
	_svgGroup2: null,
	_targetId: null,
	_colors: [],
	_globalColorScale: null,

	initialize: function initialize(options) {
		L.setOptions(this, options);
	},

	onAdd: function onAdd(map) {

		var self = this;
		this._active = true;

		// delete self-connections
		var data = this.options.data.map(function (d) {
			delete d.connections[d.properties.id];
			return d;
		});

		// the target/currently inspected site ID, and mode of inspection
		this._targetId = null;
		this._updateGlobalScale();

		// add SVG to default overlayPane, or a user specified pane
		var svg;
		if (this.options.hasOwnProperty('pane')) {
			this._mapSvg = L.svg({ pane: this.options.pane.name });
			this._mapSvg.addTo(map);
			svg = d3.select('#' + this.options.pane.elem.id).select("svg");
		} else {
			this._mapSvg = L.svg();
			this._mapSvg.addTo(map);
			svg = d3.select('#' + map.getContainer().id).select("svg");
		}

		// leaflet svg has pointer events disabled by default..
		svg.attr("pointer-events", "all");
		this._svgGroup1 = svg.append("g");
		this._svgGroup2 = this._svgGroup1.append("g");

		// add a leaflet position to each site
		data.forEach(function (site) {
			site.properties.LatLng = new L.LatLng(site.properties.lat, site.properties.lon);
		});

		if (data.length > 0) this._createSiteCircles(data);
		this._map = map;
		this._map.on("moveend viewreset", this.update, this);
		this.update();
	},

	onRemove: function onRemove(map) {
		this._active = false;
		this._mapSvg.removeFrom(map);
	},

	/*------------------------------------ PUBLIC METHODS ------------------------------------------*/

	/**
  * Trigger a redraw of all elements using current target
  */
	update: function update() {
		if (!this.isActive() || !this.options.data) return;
		var self = this;
		this._updateGlobalScale();
		self._drawConnections(this._targetId);
		if (!this._targetId || this.options.weightMode === 'GLOBAL') self._svgGroup1.selectAll("circle").style("opacity", self.options.nodeOpacity).attr("r", self.options.nodeRadius);
		this._svgGroup1.selectAll("circle").attr("transform", function (d) {
			return "translate(" + self._map.latLngToLayerPoint(d.properties.LatLng).x + "," + self._map.latLngToLayerPoint(d.properties.LatLng).y + ")";
		});
	},

	/**
  * Returns leaflet LatLngBounds of the layer
  */
	getLatLngBounds: function getLatLngBounds() {
		if (!this.options.data || !this._map) return null;
		return L.latLngBounds(this.options.data.map(function (d) {
			return [d.properties.lat, d.properties.lon];
		}));
	},


	/**
  * Update the layer with new data
  * @param {Object} data
  */
	setData: function setData(data) {
		// add a leaflet position to each site
		data.forEach(function (site) {
			site.properties.LatLng = new L.LatLng(site.properties.lat, site.properties.lon);
		});
		this._updateGlobalScale();
		this._createSiteCircles(data);
		this.options.data = data;
		if (this._active) this.update();
	},

	/**
  * Update the layer with new options
  * @param {Object} options
  */
	setOptions: function setOptions(options) {
		L.setOptions(this, options);
		if (this._active) this.update();
	},

	/**
  * Set the active target node by id
  * @param {String} id
  */
	setTarget: function setTarget(id) {
		this._targetId = id;
		if (this._active) this.update();
	},

	/**
  * Get the active target node id
  */
	getTargetId: function getTargetId() {
		return this._targetId;
	},

	/**
  * Set the layer display mode (triggers update)
  * @param mode {String} One of: ['SOURCE', 'SINK', 'ALL', 'BOTH']
  */
	setDisplayMode: function setDisplayMode(mode) {
		this.options.displayMode = mode;
		if (this._active) this.update();
	},

	/**
  * Get a node by id
  * @param id {String}
  * @returns {Object}
  */
	getPointById: function getPointById(id) {
		var data = this.options.data;
		for (var i = 0; i < data.length; i++) {
			if (id == data[i].properties.id) {
				return data[i];
			}
		}
	},

	/**
  * Test if layer is active on the map
  * @returns {boolean}
  */
	isActive: function isActive() {
		return this._active;
	},

	/**
  * Get the domain (min/max) of values in given optional data array (defaults to current)
  * @param clipped {Boolean} should domain be clipped to clipRange
  * @param data {Array} list of nodes
  * @returns {Array[min,max]}
  */
	getConnectionsDomain: function getConnectionsDomain(clipped, data) {
		var self = this;
		if (!data) data = this.options.data;
		var connections = [];
		data.forEach(function (d) {
			Object.values(d.connections).forEach(function (value) {
				if (self._connectionInRange(value) || !clipped) connections.push(value);
			});
		});

		var min = d3.min(connections);
		var max = d3.max(connections);
		return [min, max];
	},

	/*------------------------------------ PRIVATE ------------------------------------------*/

	_createSiteCircles: function _createSiteCircles(data) {

		// clear existing, create site circles
		var self = this;
		this._svgGroup1.selectAll("circle").remove();
		this._svgGroup1.selectAll("circle").data(data.map(function (d) {
			return d;
		})).attr("class", "site").enter().append("circle").style("opacity", self.options.nodeOpacity).style("cursor", "pointer").style("fill", self.options.nodeFillColor).attr("r", self.options.nodeRadius).on('click', function (d) {

			if (self.options.weightMode !== 'GLOBAL') {

				console.log(d);
				const data = d.target.__data__;
				// set circles all inactive style, set this active
				self._svgGroup1.selectAll("circle").style("opacity", self.options.nodeOpacity).attr("r", 5);
				d3.select(this).style('opacity', '1').attr("r", 10);

				// redraws ALL lines
				// TODO can probably do this more efficiently, e.g. just update style
				self._targetId = data.properties.id;
				self._drawConnections(self._targetId);
			}

			if (self.options.onClickNode) self.options.onClickNode(d);
		}).on('mouseenter', this.options.onMouseEnterNode).on('mouseleave', this.options.onMouseLeaveNode);
	},

	_updateGlobalScale: function _updateGlobalScale() {
		var _this = this;

		// init color scale, if globalScaleDomain
		// is not defined we assume we should attempt to use clipRange
		if (!this.options.globalScaleDomain) {
			this.options.globalScaleDomain = this.getConnectionsDomain(true, this.options.data);
			// arbitrarily shaving a bit of max for slightly nicer default
			this.options.globalScaleDomain[1] = this.options.globalScaleDomain[1] * 0.9;
		}
		this.options.colorScale.forEach(function (color) {
			_this._colors.push(d3.rgb(color));
		});
		this._globalColorScale = d3.scaleLinear().domain(this.options.globalScaleDomain).interpolate(d3.interpolateRgb).range(this._colors);
	},

	_drawConnections: function _drawConnections(targetId) {

		var self = this;
		var map = this._map;
		var data = this.options.data;
		var svgGroup2 = this._svgGroup2;

		svgGroup2.selectAll(".connection").remove();

		var sources = [];
		var sinks = [];

		// process connections, drawing all inactive ones
		// if weightMode=GLOBAL we draw globally weighted connections
		// if weightMode=NONE we draw simple connections
		// if weightMode=LOCAL we build array of node sites so we can compute localised scale before we draw
		data.forEach(function (site) {

			var conKeys = Object.keys(site.connections);

			// each connection
			conKeys.forEach(function (conKey) {

				var conSite = self.getPointById(conKey);
				if (!conSite || !site.connections[conKey]) return;

				// styles for connection not related to target
				var color = self.options.lineInactiveColor;
				var opacity = 0.2;
				var conValue = site.connections[conKey];
				var inRange = self._connectionInRange(conValue);

				// LOCAL scope weighting
				// we only take the target connection
				if (targetId && inRange && self.options.weightMode === 'LOCAL') {

					if (targetId === site.properties.id) {
						var target = { properties: site.properties, connections: {} };
						target.connections[conKey] = site.connections[conKey];
						sources.push(target);
						return;
					} else if (targetId === conKey) {
						var _target = { properties: site.properties, connections: {} };
						_target.connections[conKey] = site.connections[conKey];
						sinks.push(_target);
						return;
					}

					// GLOBAL visible
				} else if (self.options.weightMode === 'GLOBAL' && inRange) {

					color = self._globalColorScale(conValue);
					opacity = self.options.lineOpacity;

					// GLOBAL hidden
				} else if (self.options.weightMode === 'GLOBAL' && !inRange) {

					return;

					// NONE scope, color connections by direction
				} else if (targetId && self.options.weightMode === 'NONE' && inRange) {

					if (self.options.displayMode == 'SOURCE' && targetId == site.properties.id) {
						color = self.options.sourceColor;
						opacity = self.options.lineOpacity;
					} else if (self.options.displayMode == 'SINK' && targetId == conKey) {
						color = self.options.sinkColor;
						opacity = self.options.lineOpacity;
					} else if (self.options.displayMode == 'ANY') {
						if (targetId == site.properties.id || targetId == conKey) {
							color = self.options.allColor;
							opacity = self.options.lineOpacity;
						}
					} else if (self.options.displayMode == 'BOTH') {

						if (targetId == site.properties.id) {
							color = self.options.sourceColor;
							opacity = self.options.lineOpacity;
						}
						if (targetId == conKey) {
							color = self.options.sinkColor;
							opacity = self.options.lineOpacity;
						}
					}
				}

				// draw inactive of globally weighted line
				var targetPoint = map.latLngToLayerPoint(site.properties.LatLng);
				var conPoint = map.latLngToLayerPoint(conSite.properties.LatLng);

				// add line with event listeners
				if (self.options.weightMode !== 'NONE' && color !== self.options.lineInactiveColor) {
					svgGroup2.append("line")
						.attr("class", "connection")
						.attr("x1", targetPoint.x)
						.attr("y1", targetPoint.y)
						.attr("x2", conPoint.x)
						.attr("y2", conPoint.y)
						.attr("stroke-width", self.options.lineWidthActive)
						.attr("stroke-opacity", opacity)
						.attr("stroke", color)
						.attr("data-weight", conValue)
						.attr("data-lat", conSite.properties.LatLng.lat)
						.attr("data-lon", conSite.properties.LatLng.lng).on('mouseenter', function () {
						if (self.options.onMouseEnterLine) self.options.onMouseEnterLine(this);
					}).on('mouseleave', function () {
						if (self.options.onMouseLeaveLine) self.options.onMouseLeaveLine(this);
					});

					// no interaction
				} else {
					if (self.options.displayInactive || color !== self.options.lineInactiveColor) {
						svgGroup2.append("line").attr("class", "connection").attr("x1", targetPoint.x).attr("y1", targetPoint.y).attr("x2", conPoint.x).attr("y2", conPoint.y).attr("stroke-width", 2).attr("stroke-opacity", opacity).attr("stroke", color);
					}
				}
			});
		});

		// if we are in local weighting mode, we need to
		// calculate a localised scale for SOURCE/SINK connections
		// then use the scale to color the lines

		//  2 x color scales with independent domains, sources dashed line
		if (self.options.displayMode === 'BOTH') {

			var localSinkDomain = this.getConnectionsDomain(true, sinks);
			var sinkScale = d3.scaleLinear().domain(localSinkDomain).interpolate(d3.interpolateHcl).range(self._colors);
			this._drawLocalWeightedNodes(sinks, sinkScale, svgGroup2, self.options.lineDashStyle, 'SINK');

			var localSourceDomain = this.getConnectionsDomain(true, sources);
			var sourceScale = d3.scaleLinear().domain(localSourceDomain).interpolate(d3.interpolateHcl).range(self._colors);
			this._drawLocalWeightedNodes(sources, sourceScale, svgGroup2, null, 'SOURCE');

			// a single color scale, combined domain for ALL
		} else {
			var nodes;
			var inactive;
			switch (self.options.displayMode) {
				case 'SINK':
					nodes = sinks;
					inactive = sources;
					break;
				case 'SOURCE':
					nodes = sources;
					inactive = sinks;
					break;
				case 'ANY':
					nodes = sinks.concat(sources);
					break;
				default:
					console.error('Invalid displayMode');
					break;
			}

			var localDomain = this.getConnectionsDomain(true, nodes);
			var colorScale = d3.scaleLinear().domain(localDomain).interpolate(d3.interpolateHcl).range(self._colors);

			this._drawLocalWeightedNodes(nodes, colorScale, svgGroup2, null, self.options.displayMode);

			// draw related but inactive connections
			if (inactive) {
				inactive.forEach(function (node) {
					var conKeys = Object.keys(node.connections);
					conKeys.forEach(function (conKey) {
						var conSite = self.getPointById(conKey);
						if (!conSite || !node.connections[conKey]) return;
						var targetPoint = self._map.latLngToLayerPoint(node.properties.LatLng);
						var conPoint = self._map.latLngToLayerPoint(conSite.properties.LatLng);
						svgGroup2.append("line").attr("class", "connection").attr("x1", targetPoint.x).attr("y1", targetPoint.y).attr("x2", conPoint.x).attr("y2", conPoint.y).attr("stroke-width", self.options.lineWidth).attr("stroke-opacity", self.options.lineInactiveOpacity).attr("stroke", self.options.lineInactiveColor);
					});
				});
			}
		}
	},

	_connectionInRange: function _connectionInRange(value) {
		if (!this.options.clipRange) return true;
		return +value >= this.options.clipRange[0] && +value <= this.options.clipRange[1];
	},

	/**
  * Draw locally weighted node connections.
  * @param nodes
  * @param colorScale
  * @param svgGroup
  * @param dashStyle
  * @param conDirection {string} One of: ['SOURCE', 'SINK']
  * @private
  */
	_drawLocalWeightedNodes: function _drawLocalWeightedNodes(nodes, colorScale, svgGroup, dashStyle, conDirection) {
		console.log(nodes, colorScale, svgGroup, dashStyle, conDirection);
		var self = this;

		// dict of existing arrow head def colorKey's (unfortunately we need a new def for each color)
		// this should be unnecessary if SVG Parameters make it past spec..
		// https://www.w3.org/TR/SVGParamPrimer/ https://tabatkins.github.io/specs/svg-params/
		var arrowDefs = {};

		nodes.forEach(function (node) {

			var conKeys = Object.keys(node.connections);
			conKeys.forEach(function (conKey) {

				var conSite = self.getPointById(conKey);
				if (!conSite || !node.connections[conKey]) return;
				var conValue = node.connections[conKey];
				var targetPoint = self._map.latLngToLayerPoint(node.properties.LatLng);
				var conPoint = self._map.latLngToLayerPoint(conSite.properties.LatLng);

				var color = colorScale(conValue);
				var colorKey = color.replace(/[^0-9]/g, '');

				if (self.options.arrows && !arrowDefs.hasOwnProperty(colorKey)) {

					// add a re-usable arrowhead def for each unique polyline color
					var _arrowDef = svgGroup.append('defs');
					var _arrowMarker = _arrowDef.append('marker').attr("id", 'arrowhead-' + colorKey).attr("viewBox", "0 0 10 10").attr("refX", "5").attr("refY", "5").attr("markerUnits", "strokeWidth").attr("markerWidth", parseInt(self.options.lineWidthActive * 1.5)).attr("markerHeight", parseInt(self.options.lineWidthActive * 1.5)).attr("orient", "auto");
					_arrowMarker.append('path').attr("d", "M 0 0 L 10 5 L 0 10 z").attr("stroke", "none").attr("opacity", self.options.lineOpacity).attr("fill", color);

					arrowDefs[colorKey] = true;
				}

				svgGroup.append("polyline").attr("class", "connection").attr("offseta", "50").attr("points", targetPoint.x + ',' + targetPoint.y + ' ' + conPoint.x + ',' + conPoint.y).attr("stroke-width", self.options.lineWidthActive).attr("stroke-opacity", self.options.lineOpacity).attr("stroke", color).attr("data-weight", conValue).attr("data-lat", conSite.properties.LatLng.lat).attr("data-lon", conSite.properties.LatLng.lng).attr("data-direction", conDirection).attr("marker-mid", function () {
					if (self.options.arrows) return 'url(#arrowhead-' + colorKey + ')';
				}).attr("data-segments", function () {
					if (self.options.arrows) self._midMarkers(this, self.options.arrowSpacing);
				}).style("cursor", "pointer").style("stroke-dasharray", dashStyle).on('mouseenter', function () {
					if (self.options.onMouseEnterLine) self.options.onMouseEnterLine(this);
				}).on('mouseleave', function () {
					if (self.options.onMouseLeaveLine) self.options.onMouseLeaveLine(this);
				});
			});
		});
	},

	/**
  * Divides a polyline into segments with spacing.
  * Will produce a minimum of 2 x segments.
  * @param polyline
  * @param spacing
  * @returns {*}
  * @private
  */
	_midMarkers: function _midMarkers(polyline, spacing) {

		var svg = polyline.ownerSVGElement;

		for (var pts = polyline.points, i = 1; i < pts.numberOfItems; ++i) {

			var p0 = pts.getItem(i - 1);
			var p1 = pts.getItem(i);
			var dx = p1.x - p0.x;
			var dy = p1.y - p0.y;
			var d = Math.sqrt(dx * dx + dy * dy);
			var numSegments = Math.ceil(d / spacing);

			// ensure we have min of two segments regardless of spacing
			if (i === 1 && numSegments < 2) return this._midMarkers(polyline, spacing / 2);

			dx /= numSegments;
			dy /= numSegments;

			for (var j = numSegments - 1; j > 0; --j) {
				var pt = svg.createSVGPoint();
				pt.x = p0.x + dx * j;
				pt.y = p0.y + dy * j;
				pts.insertItemBefore(pt, i);
			}
		}
	}

});

L.networkLayer = function (options) {
	return new L.NetworkLayer(options);
};
