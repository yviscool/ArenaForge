import sublime, sublime_plugin
from sublime import PhantomSet

from .run_panel_command_mixin import RunPanelCommandMixin
from .run_panel_controller_state import RunPanelControllerState
from .package_resources import ARROW_LEFT_ICON_RESOURCE, ARROW_RIGHT_ICON_RESOURCE
from .run_panel_state import PanelTestState
from .run_panel_tester import RunPanelTester

class TestManagerCommand(RunPanelCommandMixin, sublime_plugin.TextCommand):
	BEGIN_TEST_STRING = 'Test %d {'
	OUT_TEST_STRING = ''
	END_TEST_STRING = '} rtcode %s'
	REGION_BEGIN_KEY = 'test_begin_%d'
	REGION_OUT_KEY = 'test_out_%d'
	REGION_END_KEY = 'test_end_%d'
	REGION_POS_PROP = ['', '', sublime.HIDDEN]
	REGION_ACCEPT_PROP = ['string', 'dot', sublime.HIDDEN]
	REGION_DECLINE_PROP = ['variable.c++', 'dot', sublime.HIDDEN]
	REGION_UNKNOWN_PROP = ['text.plain', 'dot', sublime.HIDDEN]
	REGION_OUT_PROP = ['entity.name.function.opd', 'bookmark', sublime.HIDDEN]
	REGION_BEGIN_PROP = ['string', ARROW_RIGHT_ICON_RESOURCE, \
				sublime.DRAW_NO_FILL | sublime.DRAW_STIPPLED_UNDERLINE | \
					sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE]
	REGION_END_PROP = ['variable.c++', ARROW_LEFT_ICON_RESOURCE, sublime.HIDDEN]
	REGION_LINE_PROP = ['string', 'dot', \
				sublime.DRAW_NO_FILL | sublime.DRAW_STIPPLED_UNDERLINE | \
					sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE]

	# Test
	# REGION_POS_PROP = REGION_UNKNOWN_PROP

	def __init__(self, view):
		self.view = view
		self.state = RunPanelControllerState(
			phantoms=PhantomSet(view, 'test-phantoms'),
			test_phantoms=[PhantomSet(view, 'test-phantoms-' + str(i)) for i in range(10)],
		)

	Test = PanelTestState

	Tester = RunPanelTester


class ModifiedListener(sublime_plugin.EventListener):
	def on_selection_modified(self, view):
		if view.get_status('opd_info') == 'opdebugger-file' and not view.settings().get('edit_mode'):
			view.run_command('test_manager', { 'action': 'sync_read_only' })

	def on_hover(self, view, point, hover_zone):
		if hover_zone == sublime.HOVER_TEXT:
			view.run_command('view_tester', { 'action': 'get_var_value', 'pos': point })

class CloseListener(sublime_plugin.EventListener):
	"""Listen to Close"""
	def __init__(self):
		super(CloseListener, self).__init__()

	def on_pre_close(self, view):
		if view.get_status('opd_info') == 'opdebugger-file':
			view.run_command('test_manager', {'action': 'close'})


class LayoutListener(sublime_plugin.EventListener):
	"""docstring for LayoutListener"""
	def __init__(self):
		super(LayoutListener, self).__init__()
	
	def move_syncer(self, view):
		w = view.window()
		if w is None:
			return

		prop = w.get_view_index(view)
		view_name = view.name() or ''
		if view_name.endswith('-run'):
			w.set_view_index(view, 1, 0)
			return

		if prop[0] != 1:
			return

		active_view = w.active_view_in_group(0)
		if active_view is None:
			return
		active_view_index = w.get_view_index(active_view)[1]
		w.set_view_index(view, 0, active_view_index + 1)
		

	# def on_load(self, view):
	# 	self.move_syncer(view)

	# def on_new(self, view):
	# 	self.move_syncer(view)
