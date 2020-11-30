

class HistoryChange {

	// freeze a past state in order to continue unroll history changes even when long promises run

	constructor(paste) {

		// make a copy to be sure
		this.paste = new URLSearchParams(paste);

	}

	todo() {
		// return true if they are all defined and at least one is modified
		var p_all_defined = true;
		var p_one_modified = false;
		for (var i = 0; i < arguments.length; i++) {
			var key = arguments[i];
			var k_exists = Boolean(hist.state.get(key));
			p_all_defined = p_all_defined && k_exists;
			var k_modified = hist.state.get(key) !== this.paste.get(key)
			p_one_modified = p_one_modified || k_modified;
		}
		return p_all_defined && p_one_modified;
	}

	_debug() {
		var stack = new Array();

		for ( let k of hist.state.keys() ) {
			var s_val = hist.state.get(k);
			if ( this.paste.has(k) ) {
				var p_val = this.paste.get(k);
				if ( s_val === p_val ) {
					stack.push('\t{0} = {1}'.format(k, s_val));
				} else {
					stack.push('\t{0} * {1} > {2}'.format(k, p_val, s_val));
				}
			} else {
				stack.push('\t{0} + {1}'.format(k, s_val));
			}
		}
		for ( let k of this.paste.keys() ) {
			var p_val = hist.state.get(k);
			if ( ! hist.state.has(k) ) {
				stack.push('\t{0} - "{1}"'.format(k, p_val));
			}
		}
		return stack.join('\n');
	}

	all_defined() {
		var p_all_defined = true;
		for (var i = 0; i < arguments.length; i++) {
			var key = arguments[i];
			var value = hist.state.get(key);
			p_all_defined = p_all_defined && ( value || value === false ) ;
		}
		return p_all_defined;
	}

	one_modified() {
		var p_one_modified = false;
		for (var i = 0; i < arguments.length; i++) {
			var key = arguments[i];
			p_one_modified = p_one_modified || ( hist.state.get(key) !== this.paste.get(key) );
		}
		return p_one_modified;
	}
}



class HistoryEngine {

	/* système de gestion de la navigation, via une interface stateless.
	
	La variable this.state contient l'état courant, this.paste l'état précédent.
	C'est en comparant les différence d'état que l'on est capable de gérer au cas par cas la mise à jour de la page.

	Il est ensuite possible d'attacher des applications, en les inscrivant dans le callback_lst.
	Elles seront alors sonnées en cas de modification de l'url
	*/

	constructor() {

		this.state = this.parse_query(); // current state
		this.paste = new URLSearchParams(''); // previous state

		this.callback_lst = new Array();

	}

	clear() {
		/* efface tout */
		this.state = new URLSearchParams();
		this.paste = new URLSearchParams('');
		
		history.replaceState('', '', '');
	}

	parse_query(url) {
		if ( url === undefined ) {
			// si aucune url n'est fournie en paramètre, prendre l'url courante
			url = window.location;
		}
		var obj = new URL(url);
		return new URLSearchParams(obj.search);
	}

	_push_to_state_as_fifo(key, value) {
		// console.log("ArtelBrowseEngine._push_state_fifo({0}, {1})".format(key, value));

		/*
		retourne 0 si le noeud existait et était déjà à la fin
		retourne 1 si le noeud n'existait pas et a été ajouté
		retourne 2 si le noeud existait mais a été replacé en haut de la pile
		*/

		if ( this.state.has(key) ) {
			var fifo = this.state.get(key).split(',');
			if ( fifo.last() == value ) {
				var retval = 0;
			} else {
				var index = fifo.indexOf(value);
				if (index > -1) {
					fifo.splice(index, 1);
					var retval = 1;
				} else {
					var retval = 2;
				}
				if (fifo.length >= 5) {
					fifo.shift();
				}
				fifo.push(value);
			}
		} else {
			var fifo = [value];
			var retval = 1;
		}
		this.state.set(key, fifo.join(','));
		return retval;
	}

	_push_to_state(nam) {
		// met à jour this.state à partir des valeurs passées en argument
		// ajoute, modifie ou supprime les paramètres d'état en fonction
		if ( nam ) {
			for ( let key of Object.keys(nam) ) {
				var value = nam[key];
				if ( value === null || value === undefined ) {
					// si la valeur est undefined ou null, la clé est supprimée
					this.state.delete(key)
				} else {
					if ( key[0] === '_' ) {
						// si la clé commence par 'undescore', c'est une fifo
						this._push_to_state_as_fifo(key, value);
					} else { // sinon c'est un scalaire
						this.state.set(key, value);
					}
				}
			}
		}
	}

	push(nam, silent) {
		// console.log("StateEngine.push_state({0})".format(JSON.stringify(nam)));

		/*
		l'argument nam est un objet json: {clef: "valeur", ... } comportant seulement les éléments
		de l'url qui doivent être modifiés
		*/

		var silent = Boolean(silent);


		if ( ! silent ) {
			// sauvegarde l'état précédent
			this.paste = new URLSearchParams(this.state);
		}


		this._push_to_state(nam);


		if ( silent ) {
			// set the new url on the same page
			history.replaceState('', '', '?' + this.state.toString());
		} else {
			this.apply();
			// set the new url as a new page
			history.pushState('', '', '?' + this.state.toString());
		}

	}

	pop(url) {
		// console.log("ArtelBrowseEngine.jump_state({0})".format(url.search));
		
		// sauvegarde l'état précédent
		this.paste = new URLSearchParams(this.state);

		// repositionne l'état courant
		this.state = new URLSearchParams(url.search);
		
		this.apply();
	}

	apply() {
		// appelle tous les callback enregistrés, pour rafraichir la page
		// extract the changes now, 

		var change = new HistoryChange( this.paste );

		for ( let callback of this.callback_lst ) {
			callback( change );
		}
	}
}

window.onpopstate = function(event) {
	hist.pop(event.target.location);
}
