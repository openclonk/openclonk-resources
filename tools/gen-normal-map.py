#!/usr/bin/python
#
# Copyright (c) Armin Burgmeier, 2014
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# This script generates a normal map from an object sprite graphics by
# scanning all pixels within a certain radius around the pixel in question,
# and treating zero alpha as an edge of the object. The radius then defines
# how "hard" the edges would be.
#
# Invocation: python gen-normal-map.py Graphics.png Normal.png

from scipy import misc
import sys

radius = 20 # TODO: This should be configurable
infile = sys.argv[1]
outfile = sys.argv[2]

img = misc.imread(infile)
print img.shape

# compute a normal vector at x/y with radius r
def get_normal(image, r, x, y):
	subimg = image[max(y-r, 0):y+r+1,max(x-r,0):x+r+1]
	x0, y0 = x - max(x-r,0) + 0.5, y - max(y-r,0) + 0.5

	xalpha = yalpha = totalpha = 0.
	for iy in range(subimg.shape[0]):
		for ix in range(subimg.shape[1]):
			length = ( (ix - x0)**2 + (iy - y0)**2)**0.5
			if length > r or length == 0:
				continue

			alpha = subimg[iy,ix,3] / 255.
			xv, yv = (ix - x0) / length, (iy - y0) / length

			xalpha += alpha * xv
			yalpha += alpha * yv
			totalpha += alpha

	length = (xalpha**2 + yalpha**2)**0.5
	if length == 0:
		return 0., 0., 1.

	if totalpha > length: # might not always be true because of rounding errors
		zlength = (totalpha**2 - length**2)**0.5
	else:
		zlength = 0.

	return -xalpha / totalpha, -yalpha / totalpha, zlength / totalpha

newimg = img.copy()
for y in range(img.shape[0]):
	for x in range(img.shape[1]):
		# skip normal map calculation for pixels that are transparent anyway
		if img[y,x,3] == 0:
			nx,ny,nz = 0., 0., 1.
		else:
			nx,ny,nz = get_normal(img, radius, x, y)

		newimg[y,x,0] = round((nx + 1.) / 2.0 * 255)
		newimg[y,x,1] = round((ny + 1.) / 2.0 * 255)
		newimg[y,x,2] = round((nz + 1.) / 2.0 * 255)
		newimg[y,x,3] = 255 # alpha

misc.imsave(outfile, newimg)
