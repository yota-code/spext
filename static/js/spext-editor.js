class SpextEditorEngine {


	constructor() {
		hist.callback_lst.push( ( change ) => this.hist_apply__callback__( change ) );

		this.load_mcp();

		this.is_modified = true;
	}

	hist_apply__callback__(change) {
		console.log( change._debug() );
	}

	load_mcp() {
		return prom_get(`_get_mcp?&b=${hist.state.get('b')}&s=${hist.state.get('s')}`).then( (obj) => {

			var h_div = document.getElementById('monaco_editor');

			this.editor = monaco.editor.create(h_div, {
				value: obj.response,
				language: 'marccup',
				wordWrap: "on",
				automaticLayout: true,
				minimap: {
					enabled: false
				}
			});

			this.editor.getModel().onDidChangeContent((event) => {
				this.is_modified = true;
			});

			setInterval(() => {
				if (this.is_modified) {
					this.load_preview();
					this.is_modified = false;
				}
			}, this.refresh_lapse);
		});
	}

	load_preview() {

		var txt = this.editor.getValue();
		return prom_post(
			`_get_preview?&b=${hist.state.get('b')}&s=${hist.state.get('s')}`,
			txt,
			'text/plain;charset=UTF-8'
		).then((obj) => {
			var h_div = document.getElementById("marccup_preview");
			h_div.innerHTML = obj.response;
			this.update_mathjax(h_div);
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
}