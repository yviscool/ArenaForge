import sublime
import sublime_plugin

from .arena_forge.adapters.sublime.shared.settings_bridge import is_lang_view


class NumberSplitter:
	def prefix_int(s):
		i = 0
		while i < len(s) and s[i].isdigit():
			i += 1
		return i

	def get_separators(s):
		i = len(s) - 1
		t = 1
		seps = []
		while i > -1:
			if t != 0 and t % 3 == 0:
				seps.append(i)
			t += 1
			i -= 1
		return sorted(seps)

	def highlight(view):
		nums = view.find_by_selector('constant.numeric.c') + \
			view.find_by_selector('constant.numeric.integer.decimal.python')
		regions = []
		for x in nums:
			s = view.substr(x)
			p = NumberSplitter.prefix_int(s)
			s = s[:p]
			seps = NumberSplitter.get_separators(s)
			seps = [y + x.a for y in seps]
			for sep in seps:
				regions.append(sublime.Region(sep, sep + 1))
		view.add_regions('number_splitter_regions', regions, 'constant.numeric.c', '', \
				sublime.DRAW_STIPPLED_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE)


def is_supported_lang(view):
	return is_lang_view(view, 'C++') or is_lang_view(view, 'Python')


class ModifyListener(sublime_plugin.EventListener):
	def on_load(self, view):
		if is_supported_lang(view):
			NumberSplitter.highlight(view)

	def on_modified(self, view):
		if is_supported_lang(view):
			NumberSplitter.highlight(view)

	def on_activated(self, view):
		if is_supported_lang(view):
			NumberSplitter.highlight(view)
