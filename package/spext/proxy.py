#!/usr/bin/env python3

import hashlib
import os

import cherrypy

from cc_pathlib import Path

import oaktree
import oaktree.proxy.html5
import oaktree.proxy.braket

import marccup
import spext.composer.html5

class SpextProxy() :

	def __init__(self, repo_dir, debug=True) :
		self.repo_dir = repo_dir
		self.debug = debug

	def get_file(self, key, local_pth) :
		""" TODO : remove all cherrypy reference """
		pth = (self.repo_dir / key / local_pth).or_archive
		if pth.suffix == '.br' :
			cherrypy.response.headers['Content-Encoding'] = 'br'
		return pth.read_bytes()

	def _get_json(self, key, name) :
		return self._get_file(key, f".cache/{name}.json")

	def mcp_to_html(self, mcp_txt, debug_dir=None) :

		b = marccup.MarccupParser(debug_dir)
		o_section = b.parse_section(mcp_txt)

		o_container = oaktree.Leaf('tmp')
		u = spext.composer.html5.Html5Composer__base__()
		u.compose(o_section, o_container)

		f = oaktree.proxy.html5.Html5Proxy(indent='', fragment=True)
		html_txt = f.save(o_container.sub[0])

		if debug_dir :
			g = oaktree.proxy.braket.BraketProxy()
			g.save(o_section, debug_dir / '4_parsed.bkt')

			(debug_dir / "5_composed.html").write_text(html_txt.replace('><', '>\n<'))

		return html_txt

	def _prep_section(self, key, ident) :

		base_dir = self.repo_dir / key
		cache_dir = base_dir / '.cache'

		local_pth = Path('part') / f'{ident:05d}'

		# read the source_file
		src_pth = base_dir / local_pth
		src_byt = src_pth.read_bytes()
		src_hsh = '<!-- {0} -->'.format(hashlib.blake2s(src_byt).hexdigest())

		# check the hash of the cached version
		dst_pth = cache_dir / local_pth
		try :
			with dst_pth.open('rt') as fid :
				dst_hsh = fid.readline().strip()
		except FileNotFoundError :
			dst_hsh = ''

		if dst_hsh != src_hsh or key == '_test':
			print(f">>> SpextProxy._prep_section({key}, {ident}) \x1b[33mPROCESSED\x1b[0m")

			src_txt = src_byt.decode('utf8')

			if key == '_test' :
				debug_dir = base_dir / '.debug' / f'{ident:05d}'
				debug_dir.make_dirs()
			else :
				debug_dir = None

			dst_txt = self.mcp_to_html(src_txt, debug_dir)

			with dst_pth.open('wt') as fid :
				fid.write(src_hsh + '\n')
				fid.write(dst_txt)

		else :
			print(f">>> SpextProxy._prep_section({key}, {ident}) \x1b[36mCACHED\x1b[0m")
