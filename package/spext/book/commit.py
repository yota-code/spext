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

import marccup.parser.book

from marccup.parser.libre import *

import Book.buildsystem

def todo(dst, * src_lst) :
	if not dst.is_file() :
		return True

	dst_time = dst.stat().st_mtime
	for src in src_lst :
		if src.stat().st_mtime >= dst_time :
			return True
	
	return False


GREEUUUG

class BookReference() :
	# maintain a list of references
	def __init__(self, base_dir) :
		self.base_dir = base_dir

		self._next_ident = 99
		self.used_ident_set = set()

	@property
	def next_ident(self) :
		self.last_ident += 1
		self.new_ident_set.add(self.last_ident)
		return self.last_ident

class BookTableOfContent() :
	# maintain the table of content
	def __init__(self, base_dir) :
		self.base_dir = base_dir

		self.toc_lst = list() # to keep track of the order of the chapters
		self.toc_map = dict()

		self.toc_pth = self.base_dir / '__doc__'
		self.toc_cache_pth = self.base_dir / '.cache/toc.json'

	def load(self) :
		line_rec = re.compile(r'^\s*(?P<depth>=+)\s*(?P<title>.*?)(\s*§(?P<ident>(\d+))?$')

		num = [0,]
		prev_depth = 1

		line_lst = self.toc_pth.read_text().splitlines()
		for n, line in enumerate(line_lst) :

			if line.lstrip().startswith('%%') : # la ligne est un commentaire
				continue
			if not line.strip() : # la ligne est vide, on passe
				continue

			line_res = line_rec.match(line)
			if line_res is None : # la ligne n'est pas un titre proprement écrit
				print(f"{toc_pth}:line {n+1}: the title line is not properly written: {line}")
				continue

			depth = len(line_res.group('depth'))
			if depth <= prev_depth + 1 :
				if depth == prev_depth + 1 :
					num += [0,]
				num = num[:depth]
				num[-1] += 1
			else :
				raise ValueError(f"{toc_pth}:line {n+1}:Title jump from level {prev_depth} to {depth}: {title}")
			prev_depth = depth

			title = line_res.group('title').strip()

			if line_res.group('ident') is None : # the ident is not known
				ident = None
			else :
				ident = int(line_res.group('ident'))
				self.toc_map[ident] = [tuple(num), title]

			self.toc_lst.append(ident) # temporaire, elle sera effacée une fois la résolution terminée

	def fill_ident(self, book_reference) :
		for n, (num, title, ident) in enumerate(self.toc_lst) :
			if ident is None :
				ident = book_reference.next_ident
				self.toc_map[ident] = [num, title]
				self.toc_lst[n] = ident

	def save(self) :
		self.toc_cache_pth.save({
			'_lst' : self.toc_lst,
			'_map' : self.toc_map
		})

		self.toc_pth.write_text('\n'.join(
			self.get_line(ident) for ident in self.toc_lst
		))

	def get_title(self, ident) :
		num, title = self.toc_map[ident]
		return '.'.join(str(i) for i in num) + f'. {title}'

	def get_line(self, ident) :
		num, title = self.toc_map[ident]
		return '=' * len(num) + f' {title} §{ident:05d}'

	


class BookKeeper() :
	""" Check and Prepare a book after a modification """

	def __init__(self, base_dir, debug=False) :
		self.base_dir = base_dir
		self.debug = debug

		self.book = marccup.parser.book.BookParser()

		# self.bs = Book.buildsystem.BuildSystem(self.base_dir, '.cache/_bs_status.json')

		self.last_ident = 0

		self.check_book() # check for ident coherency
		self.prep_book() # prepare the cache

		self.toc_pth = self.base_dir / '__doc__'

	def load(self) :

		self.section_ident_set = set()
		self.part_ident_set = set()
		self.node_ident_set = set()
		self.new_ident_set = set()
		self.title_map = dict() # ident => (num, title)

		self.update_ident()
		self.update_toc()
		self.update_part()

	def part_pth(self, ident) :
		return self.base_dir / f'part/{int(ident):05d}'

	def get_new_ident(self) :
		self.last_ident += 1
		self.new_ident_set.add(self.last_ident)
		return self.last_ident

	def check_ident(self) :
		""" do a complete check of the book, done once during the loading """

		ident_rec = re.compile(rb'§(?P<ident>(\d+|_))$', re.MULTILINE)
		title_rec = re.compile(rb'%% ^\s*(?P<depth>=+)\s*(?P<title>.*?)(\s*§(?P<ident>\d+))?$')
		section_todo = False
		part_todo_set = set()

		# read the table of content
		for ident_res in ident_rec.finditer( self.toc_pth.read_bytes() ) :
			i = ident_res.group('ident')
			if i == '_' :
				# the toc contains at least one empty ident
				section_todo = True
			else :
				self.section_ident_set(int(i))
		
		# read each existing parts
		for part_pth in (self.base_dir / 'part').glob('*') :
			s = int(part_pth.fname)
			self.part_ident_set.add()
			with part_pth.open('rb') as fid :
				first_line = fid.readline()
				if first_line.startswith(b'%%')

			byt = part_pth.read_bytes()
			for ident_res in ident_rec.finditer( byt ) :
				i = ident_res.group('ident')
				if i == '_' :
					part_todo_set.add(s)
				else :
					self.node_ident_set.add(int(i))

		self.last_ident = max(self.section_ident_set | self.node_ident_set)

		## fill the empty numbers with new ones
		empty_rec = re.compile(rb'§_$', re.MULTILINE)
		# in the toc
		if section_todo :
			txt = toc_pth.read_bytes()
			txt = empty_rec.sub(f'§{self.get_new_ident():05d}', txt)
			toc_pth.write_bytes()

		# in the parts
		for s in part_todo_set :
			pth = self.part_pth(s)
			txt = pth.read_bytes()
			txt = empty_rec.sub(f'§{self.get_new_ident():05d}', txt)
			pth.write_bytes()


	def update_part(self) :
		pass


	def update_toc(self) :

		src_pth = '__doc__'
		dst_pth = '.cache/toc.json'

		if dst_pth.is_file() :
			self.old_toc = dst_pth.load()
		else :
			self.old_toc = list()

		go, bsk = self.bs.todo([src_pth,], [dst_pth,])
	
		if not go :
			print(">>> BookCommit._update_toc() CACHE")
			return

		print(">>> BookCommit._update_toc() COMPUTE")
	
		self.new_toc = list()

		line_lst = self.bs[src_pth].splitlines()
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
				raise ValueError(f"line {n+1}:Title jump from level {prev_depth} to {depth}: {title}")

			self.ident_set.add(ident)

			self.new_toc.append([tuple(num), title, ident])
			prev_depth = depth

		dst_pth.save(self.new_toc)

		self.bs.done(* bsk)

	def update_part(self) :
		old_ident = set(ident for num, title, ident in self.old_toc)
		new_ident = set(ident for num, title, ident in self.new_toc)

	def update_reference(self, section_ident=None) :
		""" update the forward reference file : section.ident -> item.ident -> (item.space, item.tag)
		section_ident is an int, it is the ident of a section which was modified """

		dst_pth = self.base_dir / '.cache/ref.json'

		if section_ident is None or not dst_pth.is_file():
			s_lst = sorted(set(int(pth.name) for pth in (self.base_dir / 'part').glob('*')))
		else :
			s_lst = [section_ident,]
		src_pth_lst = [self.base_dir / f"part/{s:05d}" for s in s_lst]

		go, bsk = self.bs.todo(src_pth_lst, [dst_pth,])

		with dst_pth.config as db :
			for src_pth in src_pth_lst :
				print(f">>> BookCommit.update_reference({src_pth})")*

				txt = self.bs[src_pth]
				o_section = u.parse_section(txt)

				m = dict()
				for o in o_section.walk() :
					if o.ident is not None :
						p = f'{o.space}.{o.tag}' if o.space is not None else o.tag
						m[o.ident] = p
			db[int(dst_pth.fname)] = m

		self.bs.done(* bsk)
