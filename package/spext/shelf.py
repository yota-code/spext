#!/usr/bin/env python3

import collections
import datetime
import os

import cherrypy

from cc_pathlib import Path

import oaktree
import oaktree.proxy.html5
import oaktree.proxy.braket

import marccup.parser.book

from marccup.parser.libre import *

USELESS REPLACED by BOOKHANDLER


def todo(dst, * src_lst) :
	if not dst.is_file() :
		return True

	dst_time = dst.stat().st_mtime
	for src in src_lst :
		if src.stat().st_mtime >= dst_time :
			return True
	
	return False

class SpextShelf() :
	""" un objet générique, à instancier une seule fois, qui maintient la liste de tous les livres disponibles,
	permet la mise à jour des caches et la generation à la volée """
	def __init__(self, repo_dir, debug=True) :
		self.debug = debug
		self.repo_dir = repo_dir

		self.scan()

		print(self.repo_dir)
		print('\n'.join(f' * {key}' for key in sorted(self.book_set)))
		print("----")

	def scan(self) :
		self.book_set = set()
		for pth in self.repo_dir.rglob('__doc__') :

			key = str(pth.parent.relative_to(self.repo_dir))
			self.book_set.add( key )

			# create the .cache directory
			(self.repo_dir / key / '.cache' / 'part').make_dirs()

			self._prep_index( key )
			self._prep_reference( key )

		(self.repo_dir / "index.json").save(sorted(self.book_set))

	def _prep_index(self, key) :

		src_pth = self.repo_dir / key / '__doc__'

		txt = src_pth.read_text()

		u = marccup.parser.book.BookParser()

		index_lst = list()
		line_lst = txt.splitlines()
		num = [0,]
		prev_depth = 1

		for n, line in enumerate(line_lst) :
			if not line.strip() :
				continue
			title_res = title_rec.match(line)
			if title_res is None :
				print(f"error processing index line {n+1}")
				continue
			
			depth = len(title_res.group('depth'))
			title = title_res.group('title')
			ident = int(title_res.group('ident'))

			if depth <= prev_depth + 1 :
				if depth == prev_depth + 1 :
					num += [0,]
				num = num[:depth]
				num[-1] += 1
			else :
				raise ValueError()

			index_lst.append([tuple(num), title, ident])

			prev_depth = depth

		dst_pth = self.repo_dir / key / '.cache' / 'toc.json'
		dst_pth.save(index_lst)

		return index_lst

	def _check_index(self) :
		# mettre plein de vérification de cohérence, ici
		pass

	def _prep_reference(self, key) :
		""" prepare a file called reference.json which is a prefetch af cross references
		for each section, it maps a set of the ident found inside
		"""
		ref_map = collections.defaultdict(set)

		part_set = set(
			int( pth.name ) for pth in (self.repo_dir / key / 'part').glob('*')
		)

		u = marccup.parser.book.BookParser()

		for s_ident in sorted(part_set) :
			pth = self.repo_dir / key / 'part' / f'{s_ident:05d}'
			txt = pth.read_text()

			o_section = u.parse_section(txt)

			for o in o_section.walk() :
				if o.ident is not None :
					tag = o.tag if o.tag in ref_map else '__other__'
					ref_map[s_ident].add(o.ident)

			hsh = hashlib.blake2s(src_byt).hexdigest()

		stack = list()

		dst_pth = self.repo_dir / key / '.cache' / 'ref.json'
		dst_pth.save(ref_map)

		return ref_map

	def __getitem__(self, key) :
		if key not in self.book_set :
			self.install(key)
		return self.book_map[key]

if __name__ == '__main__' :
	p = BookShelf()