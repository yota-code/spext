#!/usr/bin/env python3

import pickle
import shelve

from cc_pathlib import Path

class BuildSystem() :
	""" certainly no multi thread compatible """

	NO_DESTINATION = 2
	CHANGED_SOURCE = 1
	SKIP = 0

	def __init__(self, base_dir, local_pth='.build_cache.shelve'): 
		self.base_dir = Path(base_dir)
		self.local_pth = str(local_pth)q

		pth = self.cache_pth
		pth.make_parents()

		self.file_map = dict()
		self.in_progress = dict()

	def __getitem__(self, key) :
		if key in self.file_map :
			return self.file_map[key]
		else :
			return (self.base_dir / key).read_text()

	def __str__(self) :
		with shelve.open(self.cache_pth) as db :
			return '\n'.join(f'{k}: {db[k]}' for k in sorted(db))

	@property
	def cache_pth(self) :
		return self.base_dir / self.local_pth

	def todo(self, src_pth_lst, dst_pth_lst) :
		""" return None if the file was not modified since the last time else return the content """

		# check if the destination exists
		for dst_pth in dst_pth_lst :
			pth = self.base_dir / dst_pth
			if not dst_pth.is_file() :
				return self.NO_DESTINATION, (src_pth_lst, dst_pth_lst)

		go = self.SKIP
		# check if the source was modified
		with shelve.open(self.cache_pth, protocol=pickle.HIGHEST_PROTOCOL) as db :
			for src_pth in src_pth_lst :
				pth = self.base_dir / src_pth
				byt = pth.read_bytes()
				hsh = hashlib.blake2s(byt).hexdigest()
				if local_pth not in db or db[local_pth] != hsh :
					go = self.CHANGED_SOURCE
					self.in_progress[src_pth] = hsh
				self.file_map[src_pth] = byt.decode('utf8')

		return go, (src_pth_lst, dst_pth_lst)

	def done(self, src_pth_lst, dst_pth_lst) :
		with shelve.open(self.cache_pth) as db :
			for src_pth in src_pth_lst :
				db[src_pth] = self.in_progress[src_pth]
				self.in_progress.pop(src_pth, None)
				self.file_map.pop(dst_pth, None)
			

