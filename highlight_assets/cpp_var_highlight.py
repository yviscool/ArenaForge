import re
from os import path

css = open(path.join(path.dirname(__file__), 'cpp_styles.css')).read()

DEF_TYPE = re.compile(r'int|float|double|char')
NUMBER = re.compile(r'\d+')


def safety(s):
	return s.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>').replace(' ', '&nbsp;')


def highlight(code):
	rez = '''
	<body style="margin: 0px; padding: 8px; background-color: var(--background); color: var(--foreground);">
	<style>
		%s
	</style>
	''' % css

	splited = NUMBER.split(code)
	nums = NUMBER.findall(code)
	spl3 = []

	for spl in splited:
		spl2 = DEF_TYPE.split(spl)
		nums2 = DEF_TYPE.findall(spl)
		nums2 = [('<div class="def-type">%s</div>' % num) for num in nums2]
		r = ""
		for i in range(len(spl2)):
			s = safety(spl2[i])
			if i < len(nums2):
				s += nums2[i]
			r += s
		spl3.append(r)
	splited = spl3

	nums = [('<div class="number">%s</div>' % num) for num in nums]
	for i in range(len(splited)):
		s = (splited[i])
		if i < len(nums):
			s += nums[i]
		rez += s

	rez += '</body>'
	return rez
