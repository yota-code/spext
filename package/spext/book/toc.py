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

class BookToc() :

	toc_rec = re.compile(r'^\s*(?P<depth>=+)\s*(?P<title>.*?)(\s*§(?P<ident>(\d+)))?$')

	# handle the table of content
	def __init__(self, handler) :
		self.handler = handler

		self.toc_pth = self.handler.base_dir / '__doc__'
		self.toc_cache_pth = self.handler.base_dir / '.cache/toc.json'

	def _start_check(self) :
		self.toc_lst = list() # to keep track of the order of the chapters
		self.toc_map = dict()

	def _clear_check(self) :
		""" could clean some stuffs ? but I don't know what """
		pass

	def load(self) :

		num = [0,]
		prev_depth = 1

		line_lst = self.toc_pth.read_text().splitlines()
		for n, line in enumerate(line_lst) :

			if line.lstrip().startswith('%%') : # la ligne est un commentaire
				continue
			if not line.strip() : # la ligne est vide, on passe
				continue

			toc_res = self.toc_rec.match(line)
			if toc_res is None : # la ligne n'est pas un titre proprement écrit
				print(f"{self.toc_pth}:line {n+1}: the title line is not properly written: {line}")
				continue

			depth = len(toc_res.group('depth'))
			if depth <= prev_depth + 1 :
				if depth == prev_depth + 1 :
					num = num + [0,]
				num = num[:depth]
				num[-1] += 1
			else :
				raise ValueError(f"{self.toc_pth}:line {n+1}:Title jump from level {prev_depth} to {depth}: {title}")
			prev_depth = depth

			title = toc_res.group('title').strip()

			if toc_res.group('ident') is None : # the ident is not known
				ident = None
			else :
				ident = int(toc_res.group('ident'))
				self.toc_map[ident] = [tuple(num), title]
				self.handler.ident_set.add(ident)
				
			self.toc_lst.append((num, title, ident)) # temporaire, elle sera effacée une fois la résolution terminée

	def fill_missing(self) :
		# give a section ident to title which still miss it
		for n, (num, title, ident) in enumerate(self.toc_lst) :
			if ident is None :
				ident = self.handler.next_ident
				self.toc_map[ident] = [num, title]
				self.toc_lst[n][2] = ident
				print(self.get_line(ident))


	def save(self) :
		self.toc_cache_pth.save(self.toc_lst)

		self.toc_pth.write_text('\n'.join(
			self.get_line(ident) for num, title, ident in self.toc_lst
		))

	def get_title(self, ident) :
		num, title = self.toc_map[ident]
		return '.'.join(str(i) for i in num) + f'. {title}'

	def get_line(self, ident) :
		num, title = self.toc_map[ident]
		return '=' * len(num) + f' {title} §{ident:05d}'

	