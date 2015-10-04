#!/usr/bin/env python

# Converts OGRE meshes by 90 degrees around the X axis.
# See http://forum.openclonk.org/topic_show.pl?pid=29410#pid29410

from __future__ import print_function

import subprocess
import os
import sys
import numpy
import functools

import xml.etree.ElementTree as ET


transformation = numpy.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])


devnull = open(os.devnull)
def deogrify(filename, processor):
	print('{}...'.format(filename))
	if subprocess.call(['OgreXMLConverter', filename], stdout=devnull, stderr=devnull) != 0:
		raise Exception('OgreXMLConverter failed')
	tree = ET.parse(filename + '.xml')
	processor(tree)
	tree.write(filename + '.xml')
	if subprocess.call(['OgreXMLConverter', filename + '.xml'], stdout=devnull, stderr=devnull) != 0:
		raise Exception('OgreXMLConverter failed')
	os.unlink(filename + '.xml')


def process_position(position, transformation):
	pos = numpy.array([float(position.attrib['x']), float(position.attrib['y']), float(position.attrib['z'])])
	transformed = numpy.dot(transformation, pos)
	position.attrib['x'] = str(transformed[0])
	position.attrib['y'] = str(transformed[1])
	position.attrib['z'] = str(transformed[2])

def process_normal(normal, transformation):
	# no special handling needed, as transformation has no translate
	# component.
	process_position(normal, transformation)

def process_rotation(rotation, transformation):
	axis_elem = rotation.find('axis')
	axis = numpy.array([float(axis_elem.attrib['x']), float(axis_elem.attrib['y']), float(axis_elem.attrib['z'])])
	det = numpy.linalg.det(transformation)
	transformed = det * numpy.dot(transformation, axis)
	axis_elem.attrib['x'] = str(transformed[0])
	axis_elem.attrib['y'] = str(transformed[1])
	axis_elem.attrib['z'] = str(transformed[2])

def process_scale(scale, transformation):
	scale_matrix = [[float(scale.attrib['x']), 0.0, 0.0], [0.0, float(scale.attrib['y']), 0.0], [0.0, 0.0, float(scale.attrib['z'])]]
	transformed = numpy.dot(transformation, scale_matrix, numpy.linalg.inv(transformation))
	# TODO: check non-diagonal elements to be 0
	scale.attrib['x'] = str(scale_matrix[0][0])
	scale.attrib['y'] = str(scale_matrix[1][1])
	scale.attrib['z'] = str(scale_matrix[2][2])

def process_bone(bone, transformation):
	position = bone.find('position')
	rotation = bone.find('rotation')
	scale = bone.find('scale')

	process_position(position, transformation)
	process_rotation(rotation, transformation)
	if scale is not None:
		process_scale(scale, transformation)

def process_keyframe(keyframe, transformation):
	translate = keyframe.find('translate')
	rotate = keyframe.find('rotate')
	scale = keyframe.find('scale')

	if translate is not None:
		process_position(translate, transformation)
	if rotate is not None:
		process_rotation(rotate, transformation)
	if scale is not None:
		process_scale(scale, transformation)

def process_animation(animation, transformations):
	tracks = animation.find('tracks')
	if tracks is not None:
		for track in tracks.findall('track'):
			keyframes = track.find('keyframes')
			if keyframes is not None:
				for keyframe in keyframes.findall('keyframe'):
					process_keyframe(keyframe, transformation)

def process_geometry(element, transformation):
	for vertexbuffer in element.findall('vertexbuffer'):
		for vertex in vertexbuffer.findall('vertex'):
			position = vertex.find('position')
			normal = vertex.find('normal')
			if position is not None:
				process_position(position, transformation)
			if normal is not None:
				process_normal(normal, transformation)

def process_skeleton(filename, root, transformation):
	bones = root.find('bones')
	if bones is not None:
		for bone in bones.findall('bone'):
			process_bone(bone, transformation)
	animations = root.find('animations')
	if animations is not None:
		for animation in animations.findall('animation'):
			process_animation(animation, transformation)

def process_mesh(filename, root, transformation, processed_skeletons):
	geometry = root.find('sharedgeometry')
	if geometry is not None:
		process_geometry(geometry, transformation)
	submeshes = root.find('submeshes')
	if submeshes is not None:
		for submesh in submeshes.findall('submesh'):
			geometry = submesh.find('geometry')
			if geometry is not None:
				process_geometry(geometry, transformation)
	skeletonlink = root.find('skeletonlink')
	if skeletonlink is not None:
		fullname = os.path.join(os.path.dirname(filename), skeletonlink.attrib['name'])
		if fullname not in processed_skeletons:
			processed_skeletons.add(fullname)
			deogrify(fullname, lambda x: process_skeleton(fullname, x, transformation))

processed_skeletons = set()
for mesh in sys.argv[1:]:
	filepath = os.path.abspath(mesh)
	deogrify(filepath, lambda x: process_mesh(filepath, x, transformation, processed_skeletons))
