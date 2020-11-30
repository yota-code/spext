#!/usr/bin/env python3

import datetime
import html
import os

import cherrypy

from cc_pathlib import Path

import oaktree
import oaktree.proxy.html5
import oaktree.proxy.braket

import marccup.parser.book
import marccup.composer.html5

# import spext.server.shelf
# import spext.server.proxy

class SpextServer() :

	def __init__(self, shelf=None, proxy=None) :

		self.static_dir = Path(os.environ['SPEXT_static_DIR'])
		self.repo_dir = Path(os.environ['SPEXT_repo_DIR'])

		self.shelf = shelf
		self.proxy = proxy

		self.to_html5 = marccup.composer.html5.Html5Composer()

		self.book_lst = (self.repo_dir / "index.json").load()
		
	@cherrypy.expose
	def index(self, * pos, ** nam) :
		stack = list()
		for key in sorted(self.book_lst) :
			stack.append(f'<li><a href="reader?b={key}">{key}</a></li>')
		return (self.static_dir / "html" / "index.html").read_text().format('\n'.join(stack))

	@cherrypy.expose
	def reader(self, * pos, ** nam) :
		print(f"SpextServer.reader({pos}, {nam})")
		return (self.static_dir / "html" / "reader.html").read_bytes()

	@cherrypy.expose
	def editor(self, * pos, ** nam) :
		print(f"SpextServer.editor({pos}, {nam})")
		return (self.static_dir / "html" / "editor.html").read_bytes()

	@cherrypy.expose
	def debug(self, * pos, ** nam) :
		print(f"SpextServer.debug({pos}, {nam})")
		def to_pre(pth) :
			txt = pth.read_text()
			txt = txt.replace('\t', '   ')
			txt = html.escape(txt)
			return txt
		marccup_txt = to_pre(self.repo_dir / nam['b'] / 'part' / f"{int(nam['s']):05d}")
		parsed_txt = to_pre(self.repo_dir / nam['b'] / '_tmp' / f"{int(nam['s']):05d}" / 'parsed.bkt')
		composed_txt = to_pre(self.repo_dir / nam['b'] / '.cache' / 'part' / f"{int(nam['s']):05d}")
		return (self.static_dir / "html" / "debug.html").read_text().format(marccup_txt, parsed_txt, composed_txt)

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def get_book_lst(self, * pos, ** nam) :
		return self.shelf.book_set

	def get_index(self, * pos, ** nam) :
		b = self.shelf[nam['b']]
		return

	def get_file(self, key, local_pth) :
		""" return a file directly or the .br archive of the same name """
		if key is None :
			raise cherrypy.HTTPError(400)

		if key not in self.shelf.book_set :
			raise cherrypy.HTTPError(403)

		try :
			pth = (self.repo_dir / key / local_pth).or_archive
			if pth.suffix == '.br' :
				cherrypy.response.headers['Content-Encoding'] = 'br'
			return pth.read_bytes()
		except :
			raise cherrypy.HTTPError(404)

	@cherrypy.expose
	def _get_toc(self, * pos, ** nam) :
		return self.get_file(nam.get('b', None), '.cache/toc.json')

	@cherrypy.expose
	def _get_ref(self, * pos, ** nam) :
		return self.get_file(nam.get('b', None), '.cache/ref.json')


	@cherrypy.expose
	def _get_preview(self, * pos, ** nam) :
		p = cherrypy.request.headers['Content-Length']
		txt = cherrypy.request.body.read(int(p)).decode('utf8')
		return self.proxy.mcp_to_html(txt)

	@cherrypy.expose
	def _get_section(self, * pos, ** nam) :
		
		s_ident = int(nam['s'])
		b_key = nam.get('b', None)

		local_pth = f".cache/part/{s_ident:05d}"

		self.proxy._prep_section(b_key, s_ident)

		return self.get_file(b_key, local_pth)

	@cherrypy.expose
	def _get_mcp(self, * pos, ** nam) :
		
		s_ident = int(nam['s'])
		b_key = nam.get('b', None)

		local_pth = f"part/{s_ident:05d}"

		return self.get_file(b_key, local_pth)


		# s = int(nam['s'])
		# b = self.shelf[nam['b']]
		# t = (b.base_dir / 'part' / f'{s:04d}').read_text()
		# e = b.expand_shortcut(t)

		# Path( b.base_dir / ".tmp" / f'{s:04d}.expanded.bkt').write_text(e)

		# o = b.parse_section(e)

		# g = oaktree.proxy.braket.BraketProxy()
		# k = oaktree.proxy.braket.BraketProxy(indent='')

		# g.save(o, Path( b.base_dir / ".tmp" / f'{s:04d}.parsed.bkt'))
		# k.save(o, Path( b.base_dir / ".tmp" / f'{s:04d}.parsednoindent.bkt'))

		# h = oaktree.Leaf('tmp')
		# self.to_html5.compose(o, h)

		# g.save(h.sub[0], Path( b.base_dir / ".tmp" / f'{s:04d}.composed.bkt'))
		# k.save(h.sub[0], Path( b.base_dir / ".tmp" / f'{s:04d}.composednoindent.bkt'))

		# f = oaktree.proxy.html5.Html5Proxy(indent='', fragment=True)
		# f.save(h.sub[0], Path( b.base_dir / ".tmp" / f'{s:04d}.result.html'))

		# return f.save(h.sub[0])


