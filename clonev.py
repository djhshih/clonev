#!/usr/bin/env python3

import cairo
import math

def linspace(a, b, n=100):
	if n < 2:
		return b
	diff = (float(b) - a)/(n - 1)
	return [diff * i + a  for i in range(n)]


def line(cr, src, dest):
	cr.move_to(src[0], src[1])
	cr.line_to(dest[0], dest[1])


# iscoeles triangle oriented upright, reference point at top
# theta = top angle
def isoceles_triangle(cr, pos, dx=None, dy=None, length=None, theta=None):

	if dx is None or dy is None:
		dx = length * math.cos(theta/2)
		dy = length * math.sin(theta/2)

	cr.move_to(pos[0], pos[1])
	cr.line_to(pos[0] - dx, pos[1] + dy)
	cr.line_to(pos[0] + dx, pos[1] + dy)
	cr.close_path()


def arrow(cr, src, dest, src_arrow=False, dest_arrow=True, arrow_length=3, arrow_theta=math.pi/8, filled=True):

	cr.save()

	# apply transformation

	cr.translate(src[0], src[1])

	dest = (dest[0] - src[0], dest[1] - src[1])
	src = (0, 0)
	length = math.sqrt(dest[0]**2 + dest[1]**2)

	theta = math.atan2(dest[1], dest[0])
	cr.rotate(theta)

	# draw horizonal arrow

	dest = (length, 0)
	
	dx = arrow_length * math.cos(arrow_theta)
	dy = arrow_length * math.sin(arrow_theta)

	line(cr, src, dest)
	cr.stroke()

	if filled:

		if src_arrow:
			cr.move_to(src[0], src[1])
			cr.line_to(src[0] + dx, src[1] - dy)
			cr.line_to(src[0] + dx, src[1] + dy)
			cr.close_path()

		if dest_arrow:
			cr.move_to(dest[0], dest[1])
			cr.line_to(dest[0] - dx, dest[1] - dy)
			cr.line_to(dest[0] - dx, dest[1] + dy)
			cr.close_path()

		cr.fill()

	else:
	
		if src_arrow:
			line(cr, src, (src[0] + dx, src[1] - dy))
			line(cr, src, (src[0] + dx, src[1] + dy))

		if dest_arrow:
			line(cr, dest, (dest[0] - dx, dest[1] - dy))
			line(cr, dest, (dest[0] - dx, dest[1] + dy))

		cr.stroke()

	cr.restore()


ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2

ALIGN_TOP = 0
ALIGN_MIDDLE = 1
ALIGN_BOTTOM = 2

def text(cr, string, pos, theta = 0.0, align=ALIGN_CENTER, vertical_align=ALIGN_MIDDLE, font_face = 'san serif', font_size = 10, font_slant=cairo.FONT_SLANT_NORMAL, font_weight=cairo.FONT_WEIGHT_NORMAL):
	cr.save()

	# build up an appropriate font
	cr.select_font_face(font_face , font_slant, font_weight)
	cr.set_font_size(font_size)
	fascent, fdescent, fheight, fxadvance, fyadvance = cr.font_extents()
	x_off, y_off, tw, th = cr.text_extents(string)[:4]

	if align == ALIGN_RIGHT:
		nx = -tw
	elif align == ALIGN_CENTER:
		nx = -tw/2.0
	else:
		nx = 0

	if vertical_align == ALIGN_TOP:
		ny = 0
	elif vertical_align == ALIGN_MIDDLE:
		ny = fheight/2
	else:
		ny = fheight

	cr.translate(pos[0], pos[1])
	cr.rotate(theta)
	cr.translate(nx, ny)
	cr.move_to(0,0)
	cr.show_text(string)
	cr.restore()

class Clone:

	def __init__(self, xs, ys, ws):
		self.xs = xs
		self.ys = ys
		self.ws = ws

	def stroke(self, cr, rgba, width=1):
		cr.set_source_rgba(*rgba)
		cr.set_line_width(max(cr.device_to_user_distance(width, width)))
		self.path(cr)
		cr.stroke()
	
	def fill(self, cr, rgba):
		cr.set_source_rgba(*rgba)
		self.path(cr)
		cr.fill()
	
	def path(self, cr):

		xs, ys, ws = self.xs, self.ys, self.ws

		# move to initial point
		x0, y0, w0 = xs[0], ys[0], ws[0]
		cr.move_to(x0, y0 - w0)
		
		# draw top half
		for x, y, w in zip(xs[1:], ys[1:], ws[1:]):
			x_mid = (x + x0) / 2
			cr.curve_to(x_mid, y0 - w0, x_mid, y - w, x, y - w)
			x0, y0, w0 = x, y, w

		# connect path to bottom half
		cr.line_to(xs[-1], ys[-1] + ws[-1])

		# draw bottom half
		for x, y, w in zip(reversed(xs[:-1]), reversed(ys[:-1]), reversed(ws[:-1])):
			x_mid = (x + x0) / 2
			cr.curve_to(x_mid, y0 + w0, x_mid, y + w, x, y + w)
			x0, y0, w0 = x, y, w

		# finalize path
		cr.close_path()
	
	def __str__(self):
		return 'Clone: <' + ', '.join( (str(self.xs), str(self.ys), str(self.ws)) ) + '>'

	def __repr__(self):
		return str(self)


class StreamGraph():

	def __init__(self, cr, width, height):
		self.cr = cr
		self.width = width
		self.height = height
		# top, right, bottom, left
		self.margin = (20, 60, 30, 30)

	def draw(self, clones, colours, xs, xticks, fill_labels):

		cr, width, height, margin = self.cr, self.width, self.height, self.margin

		# draw background
		cr.set_source_rgb(1.0, 1.0, 1.0)
		cr.rectangle(0, 0, width, height)
		cr.fill()

		cr.save()

		# set up drawing area
		# reference point is at (left, center)
		area_width = width - margin[3] - margin[1]
		area_height = height - margin[0] - margin[2]
		cr.translate(margin[3], margin[0] + area_height/2)
		cr.scale(area_width, area_height)

		# draw y-axis grids
		cr.set_source_rgb(0.9, 0.9, 0.9)
		cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		nyintervals=4
		for y in linspace(-0.5, 0.5, nyintervals+1):
			line(cr, (0, y), (1, y))
			cr.stroke()


		# draw clones
		for clone, colour in zip(clones, colours):
			clone.fill(cr, colour)
			#clone.stroke(cr, colour[:-1])

		# draw x-axis grids
		cr.set_source_rgb(0.6, 0.6, 0.6)
		cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		for x in xs:
			line(cr, (x, -0.54), (x, 0.5))
			cr.stroke()
		
		# draw graph box
		#cr.set_source_rgb(0.6, 0.6, 0.6)
		#cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		#cr.rectangle(0.0, -0.5, 1.0, 1.0)
		#cr.stroke()

		cr.restore()

		# set properties for axes

		xlab = 'Time'
		ylab = 'Clonal frequency'

		cr.set_source_rgb(0.0, 0.0, 0.0)
		cr.set_line_width(max(cr.device_to_user_distance(0.4, 0.4)))

		# add x-axis

		arrow(cr, (margin[3], margin[0] + area_height + 15), (margin[3] + area_width, margin[0] + area_height + 15))

		text(cr, xlab, (margin[3] + area_width/2, margin[0] + area_height + 20), font_size=6, font_weight=cairo.FONT_WEIGHT_BOLD)

		# add y-xis

		arrow(cr, (12, margin[0]), (12, margin[0] + area_height), src_arrow=True)

		text(cr, ylab, (0, margin[0] + area_height/2), theta=-math.pi/2, font_size=6, font_weight=cairo.FONT_WEIGHT_BOLD)

		# draw y-axis reference scale

		cr.set_source_rgb(0.6, 0.6, 0.6)
		cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		x = xs[1]/10 * area_width + margin[3]
		dy = float(area_height) / nyintervals
		arrow(cr, (x, 3*dy + margin[0]), (x, 4*dy + margin[0]), arrow_length=dy/6, src_arrow=True)
		text(cr, str(int(1.0/nyintervals*100)) + '%', (x + 8, 3.4*dy + margin[0]), font_size=5)

		# add x-axis tick labels

		cr.set_source_rgb(0.2, 0.2, 0.2)
		cr.set_font_size(6)
		for x, tick in zip(xs, xticks):
			xbearing, ybearing, twidth, theight, xadvance, yadvance = cr.text_extents(tick)
			cr.move_to(x*area_width - twidth/2 + margin[3], margin[0]*0.7)
			cr.show_text(tick)

		# rearrange elements for legend
		legend_labels = tuple(fill_labels[1:]) + (fill_labels[0],)
		legend_colours = tuple(colours[1:]) + (colours[0],)

		# draw fill legend
		legend(cr, (margin[3] + area_width + 10, margin[0] + 8), legend_labels, legend_colours)
		

def legend(cr, pos, labels, colours, size=5, line_spacing=2, box_spacing=2, font_size=6, font_colour=(0, 0, 0, 1)):

	cr.save()
	
	cr.set_font_size(font_size)
	cr.translate(pos[0], pos[1])

	y = 0
	for label, colour in zip(labels, colours):

		# draw box
		cr.set_source_rgba(*colour)
		cr.rectangle(0, y, size, size)
		cr.fill()

		# add label
		cr.set_source_rgba(*font_colour)
		text(cr, label, (size + box_spacing, y+1), font_size=font_size, align=ALIGN_LEFT, vertical_align=ALIGN_MIDDLE)

		y += size + line_spacing

	cr.restore()


def main():

	freqs = (
		(0.95, 0.01, 0.98),
		(0.1, 0.0025, 0.8),
		(0.0, 0.0025, 0.3), 
		(0.2, 0.0025, 0.1),
		(0.5, 0.0025, 0.1),
	)

	colours = (
		(0.95, 0.95, 0.95, 1.0),
		(0.0, 0.2, 0.0, 0.3),
		(0.0, 0.1, 1.0, 0.3),
		(0.5, 0.0, 0.0, 0.3),
		(0.5, 0.4, 0.0, 0.3),
	)

	tumour_freq = freqs[0]
	clone_freqs = freqs[1:]

	ntimes = len(clone_freqs[0]) + 1
	#nclones = len(clone_freqs)

	xticks = ('initiation', 'diagnosis', 'treatment', 'relapse')
	fill_labels = ('other clones', 'clone A', 'clone B', 'clone C', 'clone D')



	clone_ys = []
	for i in range(ntimes-1):

		# copy clone frequencies into new list to facilitate downstream computation
		fs = []
		for clone_freq in clone_freqs:
			fs.append(clone_freq[i])

		# if freq_sum > 1.0, then there must be some overlap
		freq_sum = sum(fs)
		# total spacing 'deficit'
		spacing = min(1.0 - freq_sum, 0)

		# shift to make clones centered vertically
		shift = max(1.0 - freq_sum, 0) * 0.5

		# calculate normalized frequency, skipping first element (for distributing spacing 'deficit')
		freq_sum2 = sum(fs[1:])
		gs = [0] + [f/freq_sum2 for f in fs[1:]]

		# calculate clone y positions
		ys = []
		cumy = 0
		for f, g in zip(fs, gs):
			cumy += f + (spacing * g)
			ys.append(cumy + shift)

		clone_ys.append(ys)


	# assuming that prior to first observation, all clones have same growth rate (invalid!)
	# more prevalence clones arose earlier

	# infer when clone arises based on observed prevalence, using a simple equation
	# assume all detectable clones has arisen before t = 0.5
	# time in [0, 0.5], time = (1 - p)*0.5

	clone_all = Clone(linspace(0, 1, ntimes), [0] * ntimes, [0] + [f*0.5 for f in tumour_freq])

	clones = [clone_all]
	clone_idx = 0
	for clone_freq in clone_freqs:

		xs, ys, ws = [], [], []
		t = 0
		for f in clone_freq:

			# assume that clone was present at first observation even if it was not detectable
			# (unlikely for clones to arise during the selection) between observations

			if len(xs) == 0:
				# clone is emerging
				# add point between time t and t+1
				# time since previous observation + time of previous observation
				xs.append((1 - f)*0.5 + t)
				# y location of clone: set to 0 to ensure new clones are not de novo (can be relaxed)
				ys.append(0)
				# size of clone
				ws.append(0)

			# add point at t+1
			xs.append(t+1)
			# convert reference point from (left, bottom) to (left, center)
			ys.append(clone_ys[t][clone_idx] - 0.5 - f/2)
			ws.append(f/2)

			t += 1

		# normalize times by number of time intervals
		xs = [x/float(ntimes-1) for x in xs]
		# create clone
		clones.append(Clone(xs, ys, ws))

		clone_idx += 1


	surface = cairo.SVGSurface('test.svg', 400, 100)
	cr = cairo.Context(surface)
	s = StreamGraph(cr, 400, 100)

	xs = linspace(0, 1, ntimes)
	s.draw(clones, colours, xs, xticks, fill_labels)


if __name__ == '__main__':
	main()

