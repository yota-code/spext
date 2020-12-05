#!/usr/bin/env python3

import html

from .scade import Html5Composer_Scade

def http_query(** nam) :
	return '&'.join(f'{k}={html.escape(v)}' for k, v in nam.items())

class Html5Composer__base__() :

	tr_map = {
		"paragraph" : "p",
		"table_row" : "tr",
		"page": "article"
	}
	
	def __init__(self) :
		# self.base_dir = base_dir

		self.space_map = {
			'scade' : Html5Composer_Scade()
		}

	def compose(self, child_src, parent_dst) :
		if isinstance(child_src, str) :
			parent_dst.add_text(child_src)
		else :
			if child_src.space in self.space_map :
				p = self.space_map[child_src.space]
			else :
				p = self

			if child_src.tag in p.tr_map :
				# just a translation, easy, let's do that !
				sub_dst = parent_dst.grow(
					p.tr_map[child_src.tag],
					style=set(child_src.style)
				)
				sub_continue = True
			elif hasattr(self, f"_compose_{child_src.tag}") :
				# it has a specific function, let's call it !
				sub_dst, sub_continue = getattr(p, f"_compose_{child_src.tag}")(child_src, parent_dst)
			else :
				# nothing of the above, just translate as this
				sub_dst = parent_dst.grow(child_src.tag)
				sub_continue = True

			if child_src.ident is not None :
				sub_dst.ident = f"mcp_{child_src.tag}_{child_src.ident}"
				if child_src.tag in ['paragraph', 'alinea'] :
					sub_dst.style.add('mcp-ident')

			if sub_continue :
				for sub_src in child_src.sub :
					self.compose(sub_src, sub_dst)

	def _compose_link(self, src, dst) :
		src_lst = [i.strip() for i in src.sub[0].split('|')]

		link = src_lst.pop(0)

		if '://' in link :
			sub_dst = dst.grow('a', nam={'href': link})
		else :
			if '#' in link :
				b, null, s = link.partition('#')
				link = 'reader?' + http_query(b=b, s=s)
			sub_dst = dst.grow('a', nam={'class':'mcp-link', 'href': link})

		if src_lst:
			sub_dst.add_text(src_lst.pop(0))
		else :
			sub_dst.add_text(link)

		return sub_dst, False

	def _compose_quote(self, src, dst) :
		if 'block' in src.flag :
			sub_dst = dst.grow('blockquote')
		else :
			sub_dst = dst.grow('q')
		return sub_dst, True

	def _compose_math(self, src, dst) :
		if 'block' in src.flag :
			sub_dst = dst.grow('p', style={'mcp-math',})
		else :
			sub_dst = dst.grow('span', style={'mcp-math',})

		sub_dst.add_text(''.join(src.sub))

		return sub_dst, False

	def _compose_table_cell(self, src, dst) :
		if 'header' in src.flag :
			sub_dst = dst.grow('th')
		else :
			sub_dst = dst.grow('td')
		return sub_dst, True	
