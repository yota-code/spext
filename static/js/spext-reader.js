class SpextReaderEngine {

	constructor() {

		hist.callback_lst.push( ( change ) => this.hist_apply__callback__( change ) );

		this.attach_events();

		this.toc_map = new Map();
		this.ref_map = new Map();

		if ( ! hist.state.get("b") ) {
			// if &b is not defined, no book is yet loaded, we start over from a clean state
			hist.clear();

			// and we load the list of the books
			this._book_lst__load__();
		} else {
			var h_div = document.getElementById("mcp_top").clear();
			h_div.grow('h2').add_text(hist.state.get("b"));
			hist.apply();
		}

	}

	attach_events() {
		document.getElementById("mcp_left").addEventListener('click', (evt) => {
			var [cat, ident] = evt.target.id.split('-')
			if ( evt.target.tagName === 'LI' && cat === 'section' ) {
				hist.push({'s': ident});
			}
		});
	}

	hist_apply__callback__( change ) {
		console.log( change._debug() );
		if ( change.todo('b') ) {
			Promise.all([
				this.load_toc(),
				this.load_ref()
			]).then(() => {
				hist.apply();
			})
			hist.paste.set('b', hist.state.get('b'));
			return;
		}
		if ( change.todo('s') ) {
			this.load_section();
			hist.paste.set('s', hist.state.get('s'));
			return;
		}
		if ( change.all_defined('h') ) {
			var v_ident = hist.state.get('h');
			var h_element = document.getElementById(v_ident);
			if ( Boolean(h_element) ) {
				h_element.scrollIntoView();
				h_element.classList.add("highlighted")
			} else {
				document.getElementById('mcp_main').scrollTo(0, 0);
			}
		}
	}

	_book_lst__load__() {
		// load the list of available books
		return prom_get_JSON("get_book_lst").then( (obj) => {
			var h_datalist = document.getElementById("book_lst");

			for (let line of obj) {
				h_datalist.grow('option', {'value': line});
			}
			var h_form = document.forms.book_select;
			var h_input = h_form.elements.book_pth;

			h_input.placeholder = "Please select a version";
			h_input.disabled = false;
		});
	}

	load_toc() {
		return prom_get_JSON(`_get_toc?&b=${hist.state.get('b')}`).then( (obj) => {

			this.toc_lst = obj;

			var h_div = document.getElementById("mcp_left");
			h_div.clear();

			var ol_lst = new Array();
			var li_lst = new Array();
			li_lst.push(h_div);

			var prev_length = 0;

			var n = 0;
			for (let [num, title, ident] of this.toc_lst) {

				this.toc_map.set(ident, [num, title]);

				var curr_length = num.length;

				if ( curr_length == prev_length + 1 ) {
					// console.log("STAGE ONE", num, title, ident);
					var h_li = li_lst.last();
					var h_ol = h_li.grow('ol');
					ol_lst.push(h_ol);
				} else if ( curr_length == prev_length ) {
					// console.log("STAGE TWO", num, title, ident);
					h_ol = ol_lst.last();
					li_lst.pop();
				} else {
					// console.log("STAGE THREE", num, title, ident);
					ol_lst = ol_lst.slice(0, curr_length);
					li_lst = li_lst.slice(0, curr_length);
				}

				h_li = ol_lst.last().grow('li', {id:`section-${ident}`})
				h_li.grow('strong').add_text(num.join('.') + '.');
				h_li.add_text(' ' + title);
				h_li.grow('sup', {'class': "section_n"}).add_text(`§${ident}`)
				li_lst.push(h_li)

				prev_length = curr_length;
			}
		});
	}

	load_ref() {
		return prom_get_JSON(`_get_ref?&b=${hist.state.get('b')}`).then( (obj) => {
			this.ref = obj;
		});
	}

	load_section() {
		return prom_get(`_get_section?&b=${hist.state.get('b')}&s=${hist.state.get('s')}`).then( (obj) => {

			var ident = parseInt(hist.state.get('s'));
			
			var h_div = document.getElementById("mcp_content");
			h_div.innerHTML = obj.response;

			var h_h1 = document.createElement("h1");
			var [num, title] = this.toc_map.get(ident);
			h_h1.add_text(`${num.join('.')}.\u2002${title}`);
			h_h1.grow('sup', {'class': "section_n"}).add_text(`§${ident}`);
			h_div.firstElementChild.prepend(h_h1);

			this.update_crosslink(h_div);
			this.update_reference(h_div);
			this.update_mathjax(h_div);

			var h_a = document.getElementById("quick_editor");
			h_a.setAttribute('href', "editor?" + hist.state.toString());

			var h_a = document.getElementById("quick_debug");
			h_a.setAttribute('href', "debug?" + hist.state.toString());
			h_a.hidden = false;

			hist.apply();
		});
	}

	update_mathjax(h_parent) {
		for (let h_block of h_parent.querySelectorAll("p.mcp-math")) {{
			mathjax_render(h_block.textContent.trim(), h_block, true);
		}}
	
		for (let h_inline of h_parent.querySelectorAll("span.mcp-math")) {{
			mathjax_render(h_inline.textContent.trim(), h_inline, false);
		}}
		MathJax.startup.document.clear();
		MathJax.startup.document.updateDocument();
	}

	update_crosslink(h_parent) {
		for (let h_a of h_parent.querySelectorAll("a.cross-link")) {
			var addr = h_a.getAttribute('href');
			// var res = /^([a-zA-Z]([a-zA-Z0-9\-]+)?)\/(section|figure|equation|paragraph|alinea)#([0-9]+)$/.exec(addr);
			var res = /^([a-zA-Z]([a-zA-Z0-9\-]+))?#([0-9]+)$/.exec(addr);
			if (res !== null) {
				var book = (res[1] === undefined) ? (hist.state.get('b')) : (res[1]);
				var ident = parseInt(res[3]);

				if (this.toc_map.has( ident )) {

					var [num, title] = this.toc_map.get(ident);
					h_a.setAttribute('href', `reader?b=${book}&s=${ident}`);
					h_a.setAttribute('onclick', `event.preventDefault(); hist.push({'s':'${ident}', 'b':'${book}'});`);
					h_a.clear().add_text(`${num.join('.')}.\u2002${title} `);
					h_a.grow('sup', {'class': "section_n"}).add_text(`§${ident}`);

				} else if (this.ref_map.has( ident )) {

					var [tag, section] = this.ref_map.get(ident);
					var [num, title] = this.toc_map.get(section);

					h_a.setAttribute('href', `reader?b=${book}&s=${section}&h=${tag}_${ident}`);
					h_a.setAttribute('onclick', `event.preventDefault(); hist.push({'s':'${section}', 'b':'${book}', 'h':'${tag}_${ident}'});`);
					h_a.clear().add_text(`${tag} #${ident}`);
				}
			}
		}
	}

	update_reference(h_parent) {
		console.log("SpextReaderEngine.update_reference()")
		for (let h of h_parent.querySelectorAll(".mcp-ident")) {
			var [prefix, tag, val] = h.id.split('_');
			var ident = parseInt(val);
			console.log(h.id, h.id.split('_'), tag, ident);
			if (tag === 'paragraph') {
				h.grow('br');
				h.grow('sup', {'class': `${tag}_n`}).add_text(`§${ident}`);
			} else if ( tag === 'math') {
				h.add_text(`\n\\tag{§${ident}}`);
			} else {
				h.grow('sup', {'class': `${tag}_n`}).add_text(`§${ident}`);
			}
		}
	}

}

