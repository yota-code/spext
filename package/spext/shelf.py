#!/usr/bin/env python3

import collections
import datetime
import os

import cherrypy

from cc_pathlib import Path

import oaktree
import oaktree.proxy.html5
import oaktree.proxy.braket

import spext.book

class SpextShelf() :

	""" un objet générique, à instancier une seule fois, qui maintient la liste de tous les livres disponibles,
	permet la mise à jour des caches et la generation à la volée """
	def __init__(self, repo_dir, debug=True) :
		self.repo_dir = Path(repo_dir).resolve()
		self.debug = debug

		self.book_map = dict()

	def scan(self, check=False) :
		print(f">>> SpextShelf.scan({self.repo_dir})")

		for pth in self.repo_dir.rglob('__doc__') :
			key = str(pth.parent.relative_to(self.repo_dir))
			print(f"SpextShelf.scan({key})")
			
			value = spext.book.BookHandler(pth.parent)

			if check :
				value.check()

			self.book_map[key] = value

		(self.repo_dir / "index.json").save(sorted(self.book_map))
		print(f">>> SpextShelf.scan() DONE")

if __name__ == '__main__' :
	p = BookShelf()