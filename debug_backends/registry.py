import importlib


class Debugger(object):
	"""
	Debugger
	class for basics funcs of debugger
	"""

	# write what langs supported
	# sample cpp, py, pas, ...
	supported_exts = []
	RUN_PRIOR = 0.5

	def is_pro_debug(self):
		return True

	def __init__(self, file):
		pass

	def is_runnable():
		return True

	def compile(self):
		return None

	def run(self, args):
		pass

	def set_calls(on_out, on_stop):
		pass

	def get_var_value(self, var_name, frame_id=None):
		pass

	def write(self, s):
		pass

	def terminate(self):
		pass


def get_debug_modules():
	return sorted(Debugger.__subclasses__(), key=(lambda c: c.RUN_PRIOR), reverse=True)


def get_best_debug_module(ext):
	dbgs = []
	for dbg in Debugger.__subclasses__():
		if dbg.is_runnable():
			if ext in dbg.supported_exts:
				dbgs.append(dbg)
	dbgs.sort(key=lambda dbg: dbg.RUN_PRIOR)
	dbgs.reverse()
	if dbgs:
		return dbgs[0]
	return None


importlib.import_module(f"{__package__}.cpp_osx_debugger")
