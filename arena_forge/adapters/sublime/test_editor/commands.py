import sublime_plugin
from sublime import PhantomSet, Region

from ..run_panel.logic import display_test_number
from ..run_panel.rendering import build_test_edit_header_phantom
from ..shared.package_resources import TEST_SYNTAX_RESOURCE
from .controller_state import TestEditorControllerState
from .dispatch import dispatch_test_editor_action


class TestEditCommand(sublime_plugin.TextCommand):
	def __init__(self, view):
		self.view = view
		self.state = TestEditorControllerState(
			phantoms=PhantomSet(view, 'test-phantoms'),
		)

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

	def init(self, edit, test='', source_view_id=None, test_id=None):
		v = self.view

		self.state.test_id = test_id
		self.state.source_view_id = source_view_id

		v.set_scratch(True)
		v.set_name('test ' + str(display_test_number(test_id)) + ' -edit')
		v.run_command('toggle_setting', {'setting': 'line_numbers'})
		v.run_command('set_setting', {'setting': 'fold_buttons', 'value': False})
		v.settings().set('edit_mode', True)
		v.set_syntax_file(TEST_SYNTAX_RESOURCE)
		v.insert(edit, 0, '\n' + test)
		self.update_config()

	def run(self, edit, action=None, text=None, test='', source_view_id=None, test_id=None, region=None):
		self.view.set_read_only(False)
		dispatch_test_editor_action(
			self,
			edit,
			action=action,
			text=text,
			test=test,
			source_view_id=source_view_id,
			test_id=test_id,
			region=region,
		)

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
