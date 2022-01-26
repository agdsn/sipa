 const topologyData = {
    nodes: [{
        "id": 0,
        "name": "Wu5"
    }, {
        "id": 1,
        "name": "Wu9"
    }, {
        "id": 2,
        "name": "Fl12"
    }],
    links: [{
        "source": 0,
        "target": 1,
        "ingress": 50.2,
        "egress": 50.4,
        id: 0
    },{
        "source": 1,
        "target": 2,
        "ingress": 50.2,
        "egress": 50.4,
        id: 1
    },]
};

(function(nx, global) {
    // instantiate next app
	var app = new nx.ui.Application();

	nx.define('LinkTooltip', nx.ui.Component, {
        properties: {
            link: {},
            topology: {}
        },
        view: {
            content: [
                { content: '{#link.sourceNode.id}', props: { class: "source-id" } },
                { content: '{#link.targetNode.id}', props: { class: "target-id" } },
            ],
            props: {
                class: 'link-popup-text',
            },
        }
    });

    var colorTable = ['#C3A5E4', '#75C6EF', '#CBDA5C', '#ACAEB1 ', '#2CC86F'];
    nx.define('Path.Traffic', nx.ui.Component, {
        view: {
            content: {
                name: 'topo',
                type: 'nx.graphic.Topology',
                props: {
                    adaptive: true,
                    nodeConfig: {
                        label: 'model.name',
                        iconType: "router",
                    },
                    showIcon: true,
                    data: topologyData,
                    tooltipManagerConfig: {
                        linkTooltipContentClass: 'LinkTooltip'
                    },
                    linkConfig: {
                        label: function (link) {
                            link.linkType = "test";
                            console.log(link);
                            return "";
                        },
                        width: 10,
                        color: "white",
                    },
                    autoLayout: true,
                },
                events: {
                    'topologyGenerated': '{#_path}'
                }
            }
        },
        methods: {
            _path: function(sender, events) {
                var pathLayer = sender.getLayer("paths");
                var linksLayer = sender.getLayer("links");
                var links1 = [linksLayer.getLink(0)];
                var path1 = new nx.graphic.Topology.Path({
                    pathPadding: [18, '50%'],
                    pathWidth: 8,
                    links: links1,
                    arrow: 'end'
                });
                var path2 = new nx.graphic.Topology.Path({
                    pathPadding: [18, '50%'],
                    pathWidth: 8,
                    pathStyle: {
                      'style': 'fill: red',
                    },
                    links: links1,
                    reverse: true,
                    arrow: 'end'
                });
                pathLayer.addPath(path1);
                pathLayer.addPath(path2);
            }
        }
    });

    var topology = new Path.Traffic();

	// load topology data from app/data.js
	// topology.data(topologyData);

    app.container(document.getElementById("topology-container"));

	topology.attach(app);

	console.log(topology);

})(nx, nx.global);
