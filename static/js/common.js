
/// String


Object.defineProperty(String.prototype, "format", {
	value: function() {
		var str = this.toString();
		if (arguments.length) {
			var t = typeof arguments[0];
			var args = ("string" === t || "number" === t) ? Array.prototype.slice.call(arguments) : arguments[0];
			for (let key in args) {
				str = str.replace(new RegExp("\\{" + key + "\\}", "gi"), args[key]);
			}
		}
		return str;
	}
});

/// Array

Object.defineProperty(Array.prototype, "sort_int", {
	value: function() {
		return this.sort((a, b) => a - b);
	}
});

Object.defineProperty(Array.prototype, "sort_alpha", {
	value: function() {
		return this.sort(Intl.Collator().compare);
	}
});

Object.defineProperty(Array.prototype, "isEmpty", {
	value: function() {
		return ! this.length > 0;
	}
});

Object.defineProperty(Array.prototype, "last", {
	value: function() {
		return this[this.length - 1];
	}
});

/// Element

Object.defineProperty(Element.prototype, "add_text", {
	value: function(txt) {
		this.appendChild(
			document.createTextNode(txt)
		)
		return this;
	}
});

Object.defineProperty(Element.prototype, "clear", {
	value: function() {
		while (this.lastChild) {
			this.removeChild(this.lastChild);
		}
		return this;
	}
});

Object.defineProperty(Element.prototype, "grow", {
	value: function(tag, attribute_map, name_space) {
		switch ( name_space ) {
			case "html" :
				name_space = "http://www.w3.org/1999/xhtml";
				break;
			case "svg" :
				name_space = "http://www.w3.org/2000/svg";
				break;
			case "xbl" :
				name_space = "http://www.mozilla.org/xbl";
				break;
			case "xul" :
				name_space = "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul";
				break;
		}
		
		if ( name_space !== undefined ) {
			var child = document.createElementNS(name_space, tag);
		} else {
			var child = document.createElement(tag);
		}
		
		if ( attribute_map !== undefined ) {
			for (let key in attribute_map) {
				child.setAttribute(key, attribute_map[key]);
			}
		}
		
		this.appendChild(child);
		return child;
	}
});

/// Promise

function prom_get(url) {
	// Return a new promise.
	return new Promise( function(resolve, reject) {

		// Do the usual XHR stuff
		var req = new XMLHttpRequest();
		req.open('GET', url);
		req.onload = function() {
			// This is called even on 404 etc
			// so check the status
			if (req.status == 200) {
				// Resolve the promise with the response text
				resolve( req );
			}
			else {
				// Otherwise reject with the status text
				// which will hopefully be a meaningful error
				reject( Error(req.statusText) );
			}
		};

		// Handle network errors
		req.onerror = function() {
			reject(Error("Network Error"));
		};

		// Make the request
		req.send();
	});
}

function prom_get_JSON(url) {
	return prom_get(url).then((req) => JSON.parse(req.responseText));
}

function prom_get_SVG(url) {
	return prom_get(url).then((req) => req.responseXML);
}

function prom_post(url, data, content_type) {
	// Return a new promise.
	return new Promise(function(resolve, reject) {
		// Do the usual XHR stuff
		var req = new XMLHttpRequest();
		req.open('POST', url);
		req.setRequestHeader('Content-type', content_type);
		req.onload = function() {
			// This is called even on 404 etc
			// so check the status
			if (req.status == 200) {
				// Resolve the promise with the response text
				resolve(req);
			}
			else {
				// Otherwise reject with the status text
				// which will hopefully be a meaningful error
				reject( Error(req.statusText) );
			}
		};

		// Handle network errors
		req.onerror = function() {
			reject(Error("Network Error"));
		};

		// Make the request
		req.send(data);
	});
}

function prom_post_JSON(url) {
	return prom_post(url).then((req) => JSON.parse(req.responseText));
}


function mathjax_render(input, output, display) {{
	// https://mathjax.github.io/MathJax-demos-web/input-tex2svg.html
	output.innerHTML = '';
	
	// Reset the tex labels (and automatic equation numbers, though there aren't any here).
	MathJax.texReset();

	// Get the conversion options (metrics and display settings)
	var options = MathJax.getMetricsFor(output);
	options.display = display;

	MathJax.tex2svgPromise(input, options).then(function (node) {{
		output.appendChild(node);
	}}).catch(function (err) {{
		// If there was an error, put the message into the output instead
		output.appendChild(document.createElement('pre')).appendChild(document.createTextNode(err.message));
	}}).then(function () {{
		// do nothing
	}});
}}
