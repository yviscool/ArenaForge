import sublime, sublime_plugin
from sublime import Region, PhantomSet

from .messages import translate_status_code
from .test_editor_dispatch import dispatch_test_editor_action
from .test_editor_controller_state import TestEditorControllerState
from .run_panel_rendering import build_test_edit_header_phantom
from .run_panel_state import persist_panel_tests
from .settings_bridge import base_name, get_session_repository, get_tests_file_path, infer_language_name


class TestEditCommand(sublime_plugin.TextCommand):
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
	REGION_BEGIN_PROP = ['string', 'Packages/' + base_name + '/icons/arrow_right.png', \
				sublime.DRAW_NO_FILL | sublime.DRAW_STIPPLED_UNDERLINE | \
					sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE]
	REGION_END_PROP = ['variable.c++', 'Packages/' + base_name + '/icons/arrow_left.png', sublime.HIDDEN]
	REGION_LINE_PROP = ['string', 'dot', \
				sublime.DRAW_NO_FILL | sublime.DRAW_STIPPLED_UNDERLINE | \
					sublime.DRAW_NO_OUTLINE | sublime.DRAW_EMPTY_AS_OVERWRITE]

	# Test
	# REGION_POS_PROP = REGION_UNKNOWN_PROP

	def __init__(self, view):
		self.view = view
		self.state = TestEditorControllerState(
			delta_input=0,
			tester=None,
			session=None,
			phantoms=PhantomSet(view, 'test-phantoms'),
		)

	def insert_text(self, edit, text=None):
		v = self.view
		if text is None:
			if not self.state.tester.proc_run:
				return None
			to_shove = v.substr(Region(self.state.delta_input, v.sel()[0].b))
			# print('shovel -> ', to_shove)
			v.insert(edit, v.sel()[0].b, '\n')

		else:
			to_shove = text
			v.insert(edit, v.sel()[0].b, to_shove + '\n')
		self.state.delta_input = v.sel()[0].b 
		self.state.tester.insert(to_shove + '\n')

	def insert_cb(self, edit):
		v = self.view
		s = sublime.get_clipboard()
		lst = s.split('\n')
		for i in range(len(lst) - 1):
			self.state.tester.insert(lst[i] + '\n', call_on_insert=True)
		self.state.tester.insert(lst[-1], call_on_insert=True)

	def cb_action(self, event):
		v = self.view
		if event == 'test-save':	
			for sub in v.window().views():
				if sub.id() == self.state.source_view_id:
					sub.run_command('test_manager', {
						'action': 'set_test_input',
						'data': v.substr(Region(1, v.size())),
						'id': self.state.test_id
					})
					v.close()
					break	

		elif event == 'test-delete':
			for sub in v.window().views():
				if sub.id() == self.state.source_view_id:
					sub.run_command('test_manager', {
						'action': 'delete_test',
						'id': self.state.test_id
					})
					v.close()
					break

	def update_config(self):
		self.state.phantoms.update([build_test_edit_header_phantom(self.view, self.state.test_id, self.cb_action)])

	def memorize_tests(self):
		persist_panel_tests(
			self.dbg_file,
			self.state.tester.get_tests(),
			get_session_repository(),
			infer_language_name,
			get_tests_file_path,
		)

	def change_process_status(self, status):
		# name = self.view.name()
		# self.view.set_name(name[:name.index(' ')] + ' -' + status.lower())
		self.view.set_status('process_status_code', status)
		self.view.set_status('process_status', translate_status_code(status))

	def init(self, edit, run_file=None, build_sys=None, clr_tests=False, \
		test='', source_view_id=None, test_id=None, load_session=False):
		v = self.view

		self.state.delta_input = 0
		self.state.test_id = test_id
		self.state.source_view_id = source_view_id

		v.set_scratch(True)
		v.set_name('test ' + str(test_id) + ' -edit')
		v.run_command('toggle_setting', {'setting': 'line_numbers'})
		v.run_command('set_setting', {'setting': 'fold_buttons', 'value': False})
		v.settings().set('edit_mode', True)
		v.set_syntax_file('Packages/%s/TestSyntax.sublime-syntax' % base_name)
		v.insert(edit, 0, '\n' + test)
		self.update_config()

	def sync_read_only(self):
		view = self.view
		if view.settings().get('edit_mode'):
			view.set_read_only(False)
			return
		have_sel_no_end = False
		for sel in view.sel():
			if sel.begin() != view.size():
				have_sel_no_end = True
				break

		end_cursor = len(view.sel()) and \
			((self.state.tester is None) or (not self.state.tester.proc_run)) and \
			view.size() == view.sel()[0].a

		# view.set_read_only(have_sel_no_end or end_cursor)

	def run(self, edit, action=None, run_file=None, build_sys=None, text=None, clr_tests=False, \
			test='', source_view_id=None, var_name=None, test_id=None, pos=None, \
			load_session=False, region=None, frame_id=None):
		self.view.set_read_only(False)
		should_sync = dispatch_test_editor_action(
			self,
			edit,
			action=action,
			run_file=run_file,
			build_sys=build_sys,
			text=text,
			clr_tests=clr_tests,
			test=test,
			source_view_id=source_view_id,
			var_name=var_name,
			test_id=test_id,
			pos=pos,
			load_session=load_session,
			region=region,
			frame_id=frame_id,
		)
		if should_sync:
			self.sync_read_only()

	def isEnabled(view, args):
		pass

class EditModifyListener(sublime_plugin.EventListener):
	def on_selection_modified(self, view):
		if view.settings().get('edit_mode'):
			if view.size() == 0:
				view.run_command('test_edit', {
					'action': 'replace',
					'region': [0, view.size()],
					'text': '\n'
				})

			mod = []
			change = False
			for reg in view.sel():
				if reg.a == 0:
					change = True
				mod.append(Region(max(reg.a, 1), max(reg.b, 1)))

			if change:
				view.sel().clear()
				view.sel().add_all(mod)
