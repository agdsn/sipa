window.addEventListener("pageshow", (event) => {
    var historyTraversal = event.persisted ||
	(typeof window.performance != "undefined" &&
	    window.performance.navigation.type === 2);
    if (historyTraversal) {
	// Reload page if history traversal is detected, because only input for the current
	// registration step is accepted.
	// Otherwise the forwarding to the current registration step could be interpreted
	// by the user as successful submission of the form.
	window.location.reload();
    }
});
