#!/usr/bin/env python3

import math

import argparse

import yaml
import cairo


def linspace(a, b, n=100):
	if n < 2:
		return b
	diff = (float(b) - a)/(n - 1)
	return [diff * i + a  for i in range(n)]


def path_line(cr, src, dest):
	cr.move_to(src[0], src[1])
	cr.line_to(dest[0], dest[1])


# iscoeles triangle oriented upright, reference point at top
# theta = top angle
def isoceles_triangle(cr, pos, dx=None, dy=None, length=None, theta=None, filled=True):

	if dx is None or dy is None:
		dx = length * math.cos(theta/2)
		dy = length * math.sin(theta/2)

	cr.move_to(pos[0], pos[1])
	cr.line_to(pos[0] - dx, pos[1] + dy)
	cr.line_to(pos[0] + dx, pos[1] + dy)
	cr.close_path()

	if filled:
		cr.fill()
	else:
		cr.stroke()


# arrow from source to destination
def arrow(cr, src, dest, src_arrow=False, dest_arrow=True, arrow_length=3, arrow_theta=math.pi/8, filled=True):

	cr.save()

	# apply transformation s.t. the horizontal arrow to be drawn is rotated appropriately

	cr.translate(src[0], src[1])

	# turn dest into a displacement vector, since translation has been applied
	src, dest = (0, 0), (dest[0] - src[0], dest[1] - src[1])

	theta = math.atan2(dest[1], dest[0])
	cr.rotate(theta)

	# draw horizonal arrow

	# remove angle from the dest displacement vector, since rotation has been applied
	length = math.sqrt(dest[0]**2 + dest[1]**2)
	dest = (length, 0)
	
	dx = arrow_length * math.cos(arrow_theta)
	dy = arrow_length * math.sin(arrow_theta)

	# draw main line
	path_line(cr, src, dest)
	cr.stroke()

	if filled:
		# draw triangle arrows

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
		# draw line arrows
	
		if src_arrow:
			path_line(cr, src, (src[0] + dx, src[1] - dy))
			path_line(cr, src, (src[0] + dx, src[1] + dy))

		if dest_arrow:
			path_line(cr, dest, (dest[0] - dx, dest[1] - dy))
			path_line(cr, dest, (dest[0] - dx, dest[1] + dy))

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

	# setup an appropriate font and get its properties
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

	cr.move_to(0, 0)
	cr.show_text(string)

	cr.restore()


def legend(cr, pos, labels, colours, size=5, line_spacing=2, box_spacing=2, font_size=6, font_colour=(0.0, 0.0, 0.0, 1.0)):

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

	def __init__(self, cr, width, height, margin=(20, 60, 30, 40), background_colour=(1.0, 1.0, 1.0)):
		self.cr = cr
		self.width = width
		self.height = height
		self.margin = margin
		self.background_colour = background_colour

	def draw(self, clones, colours, xs, time_labels, clone_labels, xtitle='Time', ytitle='Clonal frequency'):

		cr, width, height = self.cr, self.width, self.height
		margin_top, margin_right, margin_bottom, margin_left = self.margin

		area_width = width - margin_left - margin_right
		area_height = height - margin_top - margin_bottom

		side_left, side_top = 8, 8
		side_right = margin_left + area_width
		side_bottom = margin_top + area_height

		area_center = margin_left + area_width/2
		area_middle = margin_top + area_height/2

		# draw background
		cr.set_source_rgb(*self.background_colour)
		cr.rectangle(0, 0, width, height)
		cr.fill()


		# set up drawing area
		# reference point is at (left, center)

		cr.save()

		cr.translate(margin_left, area_middle)
		cr.scale(area_width, area_height)

		# draw y-axis grids
		cr.set_source_rgb(0.9, 0.9, 0.9)
		cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		nyintervals = 4
		for y in linspace(-0.5, 0.5, nyintervals+1):
			path_line(cr, (0, y), (1, y))
			cr.stroke()


		# draw clones
		for clone, colour in zip(clones, colours):
			clone.fill(cr, colour)
			#clone.stroke(cr, colour[:-1])

		# draw x-axis grids
		cr.set_source_rgb(0.6, 0.6, 0.6)
		cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		for x in xs:
			path_line(cr, (x, -0.54), (x, 0.5))
			cr.stroke()
		
		cr.restore()

		# set properties for axes

		cr.set_source_rgb(0.0, 0.0, 0.0)
		cr.set_line_width(max(cr.device_to_user_distance(0.4, 0.4)))

		# add x-axis

		arrow(cr, (margin_left, side_bottom + 15), (side_right, side_bottom + 15))

		text(cr, xtitle, (area_center, side_bottom + 20), font_size=6, font_weight=cairo.FONT_WEIGHT_BOLD)

		# add y-xis

		arrow(cr, (side_left + 12, margin_top), (side_left + 12, margin_top + area_height), src_arrow=True)

		text(cr, ytitle, (side_left, area_middle), theta=-math.pi/2, font_size=6, font_weight=cairo.FONT_WEIGHT_BOLD)

		# draw y-axis reference scale

		cr.set_source_rgb(0.6, 0.6, 0.6)
		cr.set_line_width(max(cr.device_to_user_distance(0.2, 0.2)))
		x = xs[1]/10 * area_width + margin_left
		dy = float(area_height) / nyintervals
		arrow(cr, (x, 3*dy + margin_top), (x, 4*dy + margin_top), arrow_length=dy/6, src_arrow=True)
		text(cr, str(int(1.0/nyintervals*100)) + '%', (x + 8, 3.4*dy + margin_top), font_size=5)

		# add x-axis tick labels

		cr.set_source_rgb(0.2, 0.2, 0.2)
		cr.set_font_size(6)
		for x, tick in zip(xs, time_labels):
			xbearing, ybearing, twidth, theight, xadvance, yadvance = cr.text_extents(tick)
			cr.move_to(x*area_width - twidth/2 + margin_left, margin_top*0.7)
			cr.show_text(tick)

		# rearrange elements for legend
		legend_labels = tuple(clone_labels[1:]) + (clone_labels[0],)
		legend_colours = tuple(colours[1:]) + (colours[0],)

		# draw fill legend
		legend(cr, (margin_left + area_width + 10, margin_top + 5), legend_labels, legend_colours)
		

# create clones based on observed clonal frequencies
# order of clones are not changed
# overlap between clones is distributed in proportion to clonal frequency (assuming minimal overlap)
# (overlap is almost surely not distributed as such, but no overlap data is available)
def create_clones(freqs):

	# first entry is contain clonal frequency combining all clones (i.e. tumour fraction)
	tumour_freq = freqs[0]
	clone_freqs = freqs[1:]

	ntimes = len(clone_freqs[0]) + 1

	# calculate y positions for clones (determine overlap between clones)
	# y positions using bottom as reference point

	clone_ys = []
	for i in range(ntimes-1):

		# copy clone frequencies into new list to facilitate downstream computation
		fs = []
		for clone_freq in clone_freqs:
			fs.append(clone_freq[i])

		purity = tumour_freq[i]
		# if freq_sum > purity, then there must be some overlap
		freq_sum = sum(fs)
		# total spacing 'deficit'
		spacing = min(purity - freq_sum, 0)

		# shift to make clones centered vertically
		if freq_sum >= purity:
			shift = (1.0 - purity) * 0.5
		else:
			#shift = (purity - freq_sum) * 0.5
			shift = (1.0 - freq_sum) * 0.5

		# calculate normalized frequency, skipping first element, since first element will not be moved
		# for distributing spacing 'deficit'
		freq_sum2 = sum(fs[1:])
		gs = [0] + [f/freq_sum2 for f in fs[1:]]

		# calculate clone y positions
		ys = []
		cumy = 0
		for f, g in zip(fs, gs):
			cumy += f + (spacing * g)
			# convert y coordinate origin from 0 to -0.5
			# convert y coordinate of reference point from (bottom) to (middle)
			y = cumy + shift - 0.5 - f/2
			# for unknown reason, y can be too small for some clone (when there is a spacing deficit)
			# use a lower bound as a hack
			# FIXME find the reason and fix this properly!
			if y - f/2 < -0.5:
				y = 0
			ys.append(y)

		clone_ys.append(ys)

	#print(clone_ys)

	# assuming that prior to first observation, all clones have same growth rate
	# (almost surely invalid, but no growth rate data is available)
	# more prevalent clones arose earlier

	# infer when clone arises based on observed prevalence, using a simple equation
	# assume all detectable clones has arisen before t = 0.5
	# time in [0, 0.5], time = (1 - p) * 0.5

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
			ys.append(clone_ys[t][clone_idx])
			ws.append(f/2)

			t += 1

		# normalize times by number of time intervals
		xs = [x/float(ntimes-1) for x in xs]
		# create clone
		clones.append(Clone(xs, ys, ws))

		clone_idx += 1

	return clones


def plot_svg(freqs, file_name, time_labels, clone_labels, clone_colours, width=400, height=100):
	
	ntimes = len(freqs[0]) + 1
	clones = create_clones(freqs)
	xs = linspace(0, 1, ntimes)

	surface = cairo.SVGSurface(file_name, width, height)
	cr = cairo.Context(surface)

	s = StreamGraph(cr, width, height)
	s.draw(clones, clone_colours, xs, time_labels, clone_labels)


def main():

	p = argparse.ArgumentParser('To plot clonal evolution streamgraphs')
	p.add_argument('input', help='input data file')
	p.add_argument('output', help='output SVG file')
	p.add_argument('--width', type=int, default=400, help='plot width')
	p.add_argument('--height', type=int, default=100, help='plot height')

	argv = p.parse_args()

	with open(argv.input, 'r') as inf:
		config = yaml.load(inf.read())

	clone_freqs = config['clone_frequencies']

	if 'time_labels' not in config.keys():
		ntimes = len(clone_freqs[0]) + 1
		config['time_labels'] = [str(x) for x in range(ntimes)]
	
	if 'clone_labels' not in config.keys():
		nclones = len(clone_freqs) - 1
		clone_labels = ['other clones']
		for i in range(nclones):
			clone_labels.append('clone ' + chr(ord('A') + i))
		config['clone_labels'] = clone_labels

	plot_svg(clone_freqs, argv.output, config['time_labels'], config['clone_labels'], config['clone_colours'], width=argv.width, height=argv.height)


if __name__ == '__main__':
	main()

