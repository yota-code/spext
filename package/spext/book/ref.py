#!/usr/bin/env python3

import collections
import datetime
import os
import re

import cherrypy

from cc_pathlib import Path

import oaktree
import oaktree.proxy.html5
import oaktree.proxy.braket

import marccup

class BookRef() :

	ident_rec = re.compile(r'§(?P<ident>(\d+|_))$', re.MULTILINE)
	empty_rec = re.compile(r'§_$', re.MULTILINE)

	# maintain a list of references
	def __init__(self, handler) :
		self.handler = handler

	def _start_check(self):
		self.section_to_item_map = dict()

	def _clear_check(self) :
		del self.part_to_fill_set

	def __iter__(self) :
		return (int(pth.fname) for pth in (self.handler.base_dir / 'part').glob('*'))

	def scan(self) :
		""" scan for ident found on parts, and note in which there is some missings """
		self.part_to_fill_set = set() # set of section ident in which an item ident is missing

		for pth in (self.handler.base_dir / 'part').glob('*') : # for every files available in part/
			try :
				s = int(pth.fname) # retrieve the section ident from the file name
			except :
				print(f"Warning: The following file is not properly named (will be moved to _trash):\n\t{pth}")

			# try to move the file if it is not properly named as a five digit integer
			std_pth = self.handler.get_part_pth(s)
			if pth != std_pth :
				if std_pth.is_file() :
					print(f"Warning: Two files have the same section ident (will be moved to _trash):\n\t{std_pth}\n\t{pth}")
					dst_pth = self.handler.base_dir / f'_trash/{pth.name}'
					dst_pth.make_parents()
					pth.rename(dst_pth)
					pth = std_pth
				else :
					pth = pth.rename(std_pth)

			if s not in self.section_to_item_map :
				self.section_to_item_map[s] = dict()
			
			txt = pth.read_text()
			for ident_res in self.ident_rec.finditer( txt ) :
				i = ident_res.group('ident')
				if i == '_' :
					self.part_to_fill_set.add(s)
				else :
					i = int(i)
					self.section_to_item_map[s][i] = None
					self.handler.ident_set.add(i)

	def fill_missing(self) :
		# give a ident to items which still miss it, and update the title in the process
		for s in self :
			pth = self.handler.get_part_pth(s)

			txt = pth.read_text().lstrip()
			if txt.startswith('%%=') :
				title, null, txt = txt.partition('\n')

			txt = txt.strip() + '\n'

			if s in self.part_to_fill_set :
				print(f"Info: missing item ident filled in {pth}")
				txt = self.empty_rec.sub((lambda res: f'§{self.handler.next_ident:05d}'), txt)

			pth.write_text(f'%%{self.handler.toc.get_line(s)}\n\n' + txt)

	def compute(self) :
		if self.handler.base_dir.name == '_test' :
			debug_dir = self.handler.base_dir / '.debug'
			debug_dir.make_dirs()
			p_indent = oaktree.proxy.braket.BraketProxy()

		else :
			debug_dir = None

		u = marccup.MarccupParser()
		for s in self :
			pth = self.handler.get_part_pth(s)
			txt = pth.read_text()

			if s not in self.section_to_item_map :
				self.section_to_item_map[s] = dict()

			o_section = u.parse_section(txt)

			# if debug_dir is not None :
			# 	p_indent.save(o_section, debug_dir / f'{s:05d}.bkt')

			for o in o_section.walk() :
				if o.ident is not None :
					tag = f'{o.space}.{o.tag}' if o.space is not None else o.tag
					self.section_to_item_map[s][int(o.ident)] = tag

		(self.handler.cache_dir / 'ref.json').save(self.section_to_item_map)

	def rebuild_cache(self, ident) :
		# scan again to get details on the nature of reference, optionnal ?
		pass