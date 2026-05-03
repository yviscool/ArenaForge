import sublime, sublime_plugin
import ast
import os
from os.path import dirname
from sublime import Region, PhantomSet
from os import path

from .debug_protocol import supports_frames
from .run_panel_controller_state import RunPanelControllerState
from .run_panel_debug_actions import (
	get_view_by_id as get_run_panel_view_by_id,
	prepare_code_view as prepare_run_panel_code_view,
	redirect_frames as redirect_run_panel_frames,
	redirect_var_value as redirect_run_panel_var_value,
	select_frame as select_run_panel_frame,
)
from .run_panel_dispatch import dispatch_test_manager_action
from .run_panel_display_actions import start_new_test, update_configs as update_run_panel_configs
from .run_panel_edit_actions import (
	apply_edit_changes as apply_run_panel_edit_changes,
	enable_edit_mode as enable_run_panel_edit_mode,
	get_begin_region as get_run_panel_begin_region,
	toggle_new_test as toggle_run_panel_new_test,
)
from .run_panel_test_actions import (
	delete_nth_test as delete_run_panel_nth_test,
	delete_test as delete_run_panel_test,
	delete_tests as delete_run_panel_tests,
	fold_accept_tests as fold_run_panel_accept_tests,
	handle_accdec_event as handle_run_panel_accdec_event,
	handle_test_event as handle_run_panel_test_event,
	open_test_edit as open_run_panel_test_edit,
	clear_all_tests as clear_run_panel_all_tests,
	set_test_input as set_run_panel_test_input,
	set_test_status as set_run_panel_test_status,
	set_tests_status as set_run_panel_tests_status,
	swap_tests as swap_run_panel_tests,
	toggle_fold as toggle_run_panel_fold,
	toggle_hide_phantoms as toggle_run_panel_hide_phantoms,
)
from .run_panel_logic import (
	should_block_test_action,
)
from .messages import product_log_message, status_message, translate, translate_status_code
from .run_panel_input_actions import push_input_history
from .root_bridge import get_debugger_info_module, get_highlight_function
from .run_panel_regions import compute_tie_pos, sync_read_only_mode
from .run_panel_rendering import build_compile_bar_phantom
from .run_panel_session_actions import clear_all as clear_run_panel, handle_process_stop, make_opd as make_run_panel
from .run_panel_session_service import save_tests_for_run
from .run_panel_state import PanelTestState
from .run_panel_tester import RunPanelTester
from .settings_bridge import base_name, get_settings, get_session_repository, infer_language_name, get_tests_file_path

debugger_info = get_debugger_info_module()


class TestManagerCommand(sublime_plugin.TextCommand):
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
		self.state = RunPanelControllerState(
			use_debugger=False,
			delta_input=0,
			tester=None,
			session=None,
			phantoms=PhantomSet(view, 'test-phantoms'),
			test_phantoms=[PhantomSet(view, 'test-phantoms-' + str(i)) for i in range(10)],
		)

	Test = PanelTestState

	Tester = RunPanelTester

	def insert_text(self, edit, text=None):
		v = self.view
		expected = v.line(self.state.delta_input).end()
		if len(v.sel()) > 1: return
		if v.sel()[0].a != expected or v.sel()[0].b != expected: return
		if text is None:
			if not self.state.tester.proc_run:
				return None
			to_shove = v.substr(Region(self.state.delta_input, v.sel()[0].b))
			v.insert(edit, v.sel()[0].b, '\n')
		else:
			to_shove = text
			v.insert(edit, v.sel()[0].b, to_shove + '\n')
		self.state.delta_input = v.sel()[0].b 
		push_input_history(self, to_shove)
		self.state.tester.insert(to_shove + '\n')

	def insert_cb(self, edit):
		v = self.view
		s = sublime.get_clipboard()
		lst = s.split('\n')
		for i in range(len(lst) - 1):
			push_input_history(self, lst[i])
			self.state.tester.insert(lst[i] + '\n', call_on_insert=True)
		push_input_history(self, lst[-1])
		self.state.tester.insert(lst[-1], call_on_insert=True)

	def toggle_fold(self, i):
		toggle_run_panel_fold(self, i)

	def open_test_edit(self, i):
		open_run_panel_test_edit(self, i)

	def get_tie_pos(self, i):
		return compute_tie_pos(self.state.tester, i)

	def on_test_action(self, i, event):
		tester = self.state.tester
		if should_block_test_action(tester.proc_run, event):
			status_message('status.action_while_running', action=event)
			return
		handle_run_panel_test_event(self, i, event)

	def on_accdec_action(self, i, event):
		handle_run_panel_accdec_event(self, i, event)

	def set_test_input(self, test=None, id=None):
		set_run_panel_test_input(self, test=test, test_id=id)

	def update_configs(self, update_last=None):
		update_run_panel_configs(self, update_last=update_last)


	def new_test(self, edit):
		start_new_test(self, edit)
	
	def memorize_tests(self):
		save_tests_for_run(
			self.state.dbg_file,
			self.state.tester.get_tests(),
			get_session_repository(),
			infer_language_name,
			get_tests_file_path,
		)

	def on_insert(self, s):
		self.view.run_command('test_manager', {'action': 'insert_opd_input', 'text': s})

	def on_out(self, s):
		v = self.view

		self.view.run_command('test_manager', {'action': 'insert_opd_out', 'text': s})

		if not self.state.out_region_set:
			self.state.out_region_set = True

	def add_region(self, line, region_prop):
		v = self.view
		pos = v.line(line)
		from random import randint
		v.add_regions(str(randint(0, 1e9)), [Region(pos.a, pos.a + 1)], *region_prop)

	def on_stop(self, rtcode, runtime, crash_line=None):
		handle_process_stop(self, rtcode, runtime, crash_line=crash_line)

	def redirect_var_value(self, var_name, pos=None):
		redirect_run_panel_var_value(self, var_name, pos=pos)

	def redirect_frames(self):
		redirect_run_panel_frames(self)

	def select_frame(self, id):
		select_run_panel_frame(self, id)

	def toggle_side_bar(self):
		self.view.window().run_command('toggle_side_bar')

	def set_test_status(self, nth, accept=True, call_tester=True):
		set_run_panel_test_status(self, nth, accept=accept, call_tester=call_tester)

	def set_tests_status(self, accept=True):
		set_run_panel_tests_status(self, accept=accept)

	def fold_accept_tests(self):
		fold_run_panel_accept_tests(self)

	def change_process_status(self, status):
		self.view.set_status('process_status_code', status)
		self.view.set_status('process_status', translate_status_code(status))

	def clear_all(self):
		clear_run_panel(self)

	def set_compile_bar(self, cmd, type=''):
		self.state.test_phantoms[0].update([build_compile_bar_phantom(self.view, cmd, type=type)])

	def get_view_by_id(self, id):
		return get_run_panel_view_by_id(self, id)

	def prepare_code_view(self):
		prepare_run_panel_code_view(self)

	def make_opd(self, edit, run_file=None, build_sys=None, clr_tests=False, \
		sync_out=False, code_view_id=None, use_debugger=False, load_session=False):
		make_run_panel(
			self,
			edit,
			run_file=run_file,
			build_sys=build_sys,
			clr_tests=clr_tests,
			sync_out=sync_out,
			code_view_id=code_view_id,
			use_debugger=use_debugger,
			load_session=load_session,
		)

	def delete_nth_test(self, edit, nth, fixed_end=None):
		delete_run_panel_nth_test(self, edit, nth, fixed_end=fixed_end)

	def delete_test(self, edit, id):
		delete_run_panel_test(self, edit, id)

	def get_style_test_status(self, nth):
		check = self.state.tester.check_test(nth)
		if check:
			return self.REGION_ACCEPT_PROP
		elif check is False:
			return self.REGION_DECLINE_PROP
		return self.REGION_UNKNOWN_PROP

	def renumerate_tests(self, edit, max_nth_test):
		'''
		renumerating tests
		sample if 
			[test 2, test 5] -> [test 1, test 2]
		uses after del_tests
		'''
		v = self.view
		cur_nth = 0
		for i in range(0, max_nth_test):
			begin_key = self.REGION_BEGIN_KEY % i
			rs_beg = v.get_regions(begin_key)
			if rs_beg:
				rs_beg = rs_beg[0]
				# v.replace(edit, v.word(rs_beg.begin() + 5), str(cur_nth + 1))
				v.erase_regions(begin_key)
				v.add_regions(self.REGION_BEGIN_KEY % (cur_nth), [rs_beg], \
					*self.REGION_BEGIN_PROP)

				rs_line = v.get_regions('line_%d' % cur_nth)

				v.erase_regions('line_%d' % i)
				v.add_regions('line_%d' % cur_nth, rs_line, \
					*self.REGION_LINE_PROP)


				end_key = self.REGION_END_KEY % i
				rs_end = v.get_regions(end_key)
				if rs_end:
					rs_end = rs_end[0]
					v.erase_regions(end_key)
					v.add_regions(self.REGION_END_KEY % (cur_nth), [rs_end], \
						*self.REGION_END_PROP)

				cur_nth += 1

	def delete_tests(self, edit):
		delete_run_panel_tests(self, edit)

	def sync_read_only(self):
		sync_read_only_mode(self.view, self.state.tester, self.state.delta_input)

	def enable_edit_mode(self):
		enable_run_panel_edit_mode(self)

	def get_begin_region(self, id):
		return get_run_panel_begin_region(self, id)

	def apply_edit_changes(self):
		apply_run_panel_edit_changes(self)

	def toggle_new_test(self):
		toggle_run_panel_new_test(self)

	def swap_tests(self, edit, dir=-1):
		swap_run_panel_tests(self, edit, direction=dir)

	def toggle_hide_phantoms(self):
		toggle_run_panel_hide_phantoms(self)

	def clear_all_tests(self):
		clear_run_panel_all_tests(self)

	def run(self, edit, action=None, run_file=None, build_sys=None, text=None, clr_tests=False, \
			sync_out=False, code_view_id=None, var_name=None, use_debugger=False, pos=None, \
			load_session=False, region=None, frame_id=None, data=None, id=None, dir=1):
		self.view.set_read_only(False)
		should_sync = dispatch_test_manager_action(
			self,
			edit,
			action=action,
			run_file=run_file,
			build_sys=build_sys,
			text=text,
			clr_tests=clr_tests,
			sync_out=sync_out,
			code_view_id=code_view_id,
			var_name=var_name,
			use_debugger=use_debugger,
			pos=pos,
			load_session=load_session,
			region=region,
			frame_id=frame_id,
			data=data,
			id=id,
			dir=dir,
		)
		if should_sync:
			self.sync_read_only()

	def isEnabled(view, args):
		pass


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
		try:
			w = view.window()
			prop = w.get_view_index(view)
			# print(view.name())
			if view.name()[-4:] == '-run':
				w.set_view_index(view, 1, 0)
				# print('moved to second group')
			elif prop[0] == 1:
				active_view_index = w.get_view_index(w.active_view_in_group(0))[1]
				# print('moved to first group')
				w.set_view_index(view, 0, active_view_index + 1)
		except:
			pass
		

	# def on_load(self, view):
	# 	self.move_syncer(view)

	# def on_new(self, view):
	# 	self.move_syncer(view)
