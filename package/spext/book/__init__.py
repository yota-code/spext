#!/usr/bin/env python3

import datetime

from cc_pathlib import Path

import spext.book.toc
import spext.book.ref

class BookHandler() :
	""" cette classe permet de manipuler les livres,
	elle devrait être chargé une fois pour chacun d'eux :
	* pour mettre à jour le cache
	* pour effectuer des vérifications

	pour les accès rapides (en statique ou en dynamique) il est important de s'appuyer sur le fichiers du cache
	"""
	def __init__(self, base_dir) :
		self.base_dir = Path(base_dir).resolve()

		self.toc = spext.book.toc.BookToc(self)
		self.ref = spext.book.ref.BookRef(self)

		self.cache_dir = self.base_dir / '.cache'
		self.cache_dir.make_dirs()

		(self.cache_dir / 'part').make_dirs()

		self.log_pth = None

		self.ident_set = None
		self._last_ident = None

	@property
	def next_ident(self) :
		self._last_ident += 1
		if self.ident_set is not None :
			if self._last_ident in self.ident_set :
				self.log(f"Error: Duplicate ident: {self._last_ident}")
			self.ident_set.add(self.last_ident)
		return self._last_ident

	def _start_check(self) :

		self.log_pth = self.base_dir / 'check.log'
		self.log_pth.write_text('')
		self.log(f"{datetime.datetime.now()} >>> BookHandler.check()")

		self.ident_set = set()

		self.toc._start_check()
		self.ref._start_check()

	def _clear_check(self) :

		self.ref._clear_check()
		self.toc._clear_check()

		self.log_pth = None

	def log(self, * pos) :
		if self.log_pth is not None :
			with self.log_pth.open('at') as fid :
				print(* pos, file=fid)
		print(* pos)

	def get_part_pth(self, ident) :
		return self.base_dir / f'part/{ident:05d}'

	def check(self) :
		""" procède à une vérification générale et en profondeur du livre ainsi qu'à la mise à jour du cache
		génèrera un fichier d'erreur
		
		"""

		self._start_check()

		self.toc.load()
		self.ref.scan()

		self._last_ident = max(self.ident_set)
		self.ident_set = None

		self.toc.fill_missing()

		self._clean_parts()

		self.ref.fill_missing()

		self.ref.compute()
		self.toc.save()

		self._clear_check()


	def update_part(self, s_ident) :
		""" procède à la vérification limitée à la seule partie modifiée """
		pass

	def update_toc(self) :
		pass


	def _clean_parts(self) :
		# check for coherence between the toc and already existing parts
		section_ident_set = self.toc.toc_map.keys()
		part_ident_set = set(
			int(pth.fname) for pth in (self.base_dir / 'part').glob('*')
		)

		part_to_be_created = section_ident_set - part_ident_set
		if part_to_be_created :
			self.log("Warning: the following parts are referenced but are missing (will be created empty):")
			for ident in part_to_be_created :
				self.log(f"\t+ part/{ident:05d}")
				self.get_part_pth(ident).write_text(f'%%= {self.toc.get_title(ident)}\n\n')
				part_ident_set.add(ident)

		part_to_be_deleted = part_ident_set - section_ident_set
		if part_to_be_deleted :
			self.log("Warning: the following parts are not referenced anymore (will be moved to _trash):")
			(self.base_dir / '_trash').make_dirs()
			for ident in part_to_be_deleted :
				self.log(f"\t- part/{ident:05d}")
				dst_pth = self.base_dir / f'_trash/{ident:05d}'
				dst_pth.make_parents()
				self.get_part_pth(ident).rename(dst_pth)
