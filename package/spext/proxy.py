#!/usr/bin/env python3

import hashlib
import os

import cherrypy

from cc_pathlib import Path

import oaktree
import oaktree.proxy.html5
import oaktree.proxy.braket

import marccup.parser.generic
import spext.composer.artel

class SpextProxy() :

	def __init__(self, repo_dir, debug=True) :
		self.debug = debug
		self.repo_dir = repo_dir

	def get_file(self, key, local_pth) :
		pth = (self.repo_dir / key / local_pth).or_archive
		if pth.suffix == '.br' :
			cherrypy.response.headers['Content-Encoding'] = 'br'
		return pth.read_bytes()

	def _get_json(self, key, name) :
		return self._get_file(key, f".cache/{name}.json")

	def mcp_to_html(self, mcp_txt, debug_dir=None) :
		""" convert a marccup file into and html"""
		b = marccup.parser.generic.GenericParser()
		u = spext.composer.artel.ArtelComposer__base__()

		o_section = b.parse(mcp_txt)
		o_container = oaktree.Leaf('tmp')
		u.compose(o_section, o_container)

		f = oaktree.proxy.html5.Html5Proxy(indent='', fragment=True)

		if debug_dir is not None:
			g = oaktree.proxy.braket.BraketProxy()
			g.save(o_section, debug_dir / 'parsed.bkt')

			k = oaktree.proxy.braket.BraketProxy(indent='')
			k.save(o_section, debug_dir / 'parsed_noindent.bkt')

		html_txt = f.save(o_container.sub[0])
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
				debug_dir = base_dir / '_tmp' / f'{ident:05d}'
				debug_dir.make_dirs()
			else :
				debug_dir = None

			dst_txt = self.mcp_to_html(src_txt, debug_dir)



			# if self.debug :

			# 	tmp_dir = base_dir / '_tmp'
			# 	tmp_dir.make_dirs()

			# 	g = oaktree.proxy.braket.BraketProxy()
			# 	k = oaktree.proxy.braket.BraketProxy(indent='')

			# 	g.save(o, tmp_dir / f'{ident:05d}.parsed.bkt')
			# 	k.save(o, tmp_dir / f'{ident:05d}.parsednoindent.bkt')

			# m = oaktree.Leaf('tmp')
			# u.compose(o, m)

			#g.save(h.sub[0], Path( base_dir / ".tmp" / f'{ident:04d}.composed.bkt'))
			#k.save(h.sub[0], Path( base_dir / ".tmp" / f'{ident:04d}.composednoindent.bkt'))

			# f = oaktree.proxy.html5.Html5Proxy(indent='', fragment=True)
			#f.save(h.sub[0], Path( base_dir / ".tmp" / f'{ident:04d}.result.html'))

			with dst_pth.open('wt') as fid :
				fid.write(src_hsh + '\n')
				fid.write(dst_txt)

		else :
			print(f">>> SpextProxy._prep_section({key}, {ident}) \x1b[36mCACHED\x1b[0m")