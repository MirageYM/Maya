# -*- coding: utf-8 -*-
'''
Dummy Mentalray Material Class Generator scripts

Copyright (c) 2019, yasutoshi Mori All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

from maya.OpenMaya import *
import sys
import os

class DummyBuilder(object):
	def __init__(self):
		super(DummyBuilder,self).__init__()
		self.outs_ = []
		self.typeId = 0

	def build(self, obj, dummyClassName, basePath):
		f = MFnDependencyNode(obj)
		typeName = f.typeName()

		self.typeId = f.typeId().id()

		self.createClass(dummyClassName,typeName)

		rejectAttrNames = [
			'message',
			'caching',
			'frozen',
			'nodeState'
		]
		
		for i in range(f.attributeCount()):
			fnAttr = MFnAttribute(f.attribute(i))
			if( fnAttr.name() in rejectAttrNames ):
				continue
			addCmd = fnAttr.getAddAttrCmd()
			self.addCmdToCreateAttr(addCmd,dummyClassName)

		self.writeFile(basePath,dummyClassName)
		
	def createClass(self,dummyClassName,typeName):
		self.outs_.append(R'class %s( OpenMayaMPx.MPxNode ):' % dummyClassName )
		self.outs_.append(R'    kPluginNodeName = "%s"' % typeName )
		self.outs_.append(R'    kPluginNodeClassify = "shader/surface"')
		self.outs_.append(R'    PluginNodeId = OpenMaya.MTypeId(%d)' % self.typeId)
		self.outs_.append(R'    def __init__( self ):')
		self.outs_.append(R'        OpenMayaMPx.MPxNode.__init__(self)')
		self.outs_.append(R'    def compute(self, plug, block):')
		self.outs_.append(R'        return OpenMaya.kUnknownParameter')
		self.outs_.append(R'    @staticmethod')
		self.outs_.append(R'    def nodeCreator():')
		self.outs_.append(R'        return OpenMayaMPx.asMPxPtr(%s() )'%dummyClassName)
		self.outs_.append(R'    @staticmethod')
		self.outs_.append(R'    def nodeInitializer():')
		self.outs_.append(R'        nAttr = OpenMaya.MFnNumericAttribute()')
		self.outs_.append(R'        eAttr = OpenMaya.MFnEnumAttribute()')
		self.outs_.append(R'        mAttr = OpenMaya.MFnMessageAttribute()')
		self.outs_.append(R'        try:')
		self.outs_.append(R'            %s.aOutColor = nAttr.createColor("outColor", "oc")' % dummyClassName)
		self.outs_.append(R'            nAttr.setStorable(0)')
		self.outs_.append(R'            nAttr.setHidden(0)')
		self.outs_.append(R'            nAttr.setReadable(1)')
		self.outs_.append(R'            nAttr.setWritable(0)')
		self.outs_.append(R'            %s.addAttribute(%s.aOutColor)' % (dummyClassName,dummyClassName))
		self.outs_.append(R'        except:')
		self.outs_.append(R'            pass')
		
	def addCmdToCreateAttr(self, addCmd, dummyClassName):
		s = addCmd.split(' ')[1:len(addCmd)-1]
		args = {}
		for i in range(len(s)):
			if( '-' in s[i] ):
				args[s[i].replace('-','')] = s[i+1].replace('"','').replace(';','')
				i += 1

		if( 'at' not in args):
			return

		createLine = None
		if( args['at'] == 'float'):
			createLine = R'            %s.%s = nAttr.create("%s","%s",MFnNumericData.kDouble)' % (dummyClassName,args['ln'],args['ln'],args['sn'])
		elif( args['at'] == 'bool'):
			createLine = R'            %s.%s = nAttr.create("%s","%s",MFnNumericData.kBoolean)' % (dummyClassName,args['ln'],args['ln'],args['sn'])
		elif( args['at'] == 'long'):
			createLine = R'            %s.%s = nAttr.create("%s","%s",MFnNumericData.kLong)' % (dummyClassName,args['ln'],args['ln'],args['sn'])
		elif( args['at'] == 'float3'):
			createLine = R'            %s.%s = nAttr.createColor("%s","%s")' % (dummyClassName,args['ln'],args['ln'],args['sn'])
		elif( args['at'] == 'enum'):
			createLine = R'            %s.%s = eAttr.create("%s","%s")' % (dummyClassName,args['ln'],args['ln'],args['sn'])
		elif( args['at'] == 'message'):
			createLine = R'            %s.%s = mAttr.create("%s","%s")' % (dummyClassName,args['ln'],args['ln'],args['sn'])

		if( createLine is None ):
			return
		
		self.outs_.append(R'        try:')
		self.outs_.append(createLine)
		self.outs_.append(R'            %s.addAttribute(%s.%s)' % (dummyClassName,dummyClassName,args['ln']) )
		self.outs_.append(R'        except:')
		self.outs_.append(R'            pass')


	def writeFile(self,basePath,dummyClassName):
		with open( os.path.join( basePath, dummyClassName + '.py' ), 'w' ) as fhdl:
			fhdl.write('import maya.OpenMaya as OpenMaya\n')
			fhdl.write('import maya.OpenMayaMPx as OpenMayaMPx\n')
			for o in self.outs_:
				fhdl.write(o + '\n')


def addRegisterCmd(fhdl, dummyClassName):
	fhdl.write( 
	R"""
	try:
		mplugin.registerNode( %s.kPluginNodeName, 
							  %s.PluginNodeId, 
							  %s.nodeCreator, 
							  %s.nodeInitializer, 
							  OpenMayaMPx.MPxNode.kDependNode, 
							  %s.kPluginNodeClassify )
	except:
		sys.stderr.write( "Failed to register node: %s" )
		raise
""" % ( dummyClassName,dummyClassName,dummyClassName,dummyClassName,dummyClassName,dummyClassName) )

def addDeregisterCmd(fhdl, dummyClassName):
	fhdl.write( 
	R"""
	try:
		mplugin.deregisterNode( %s.PluginNodeId )
	except:
		sys.stderr.write( "Failed to deregister node: %s" )
		raise
""" % ( dummyClassName,dummyClassName ) )

def doIt( basePath ):

	createShaders = (
		( 'mia_material', 'MiaMaterialDummy' ),
		( 'mia_material_x', 'MiaMaterialXDummy' ),
		( 'mia_material_x_passes', 'MiaMaterialXPassesDummy' )
	)

	for shaderName, dummyClassName in createShaders:
		dgModifier = MDGModifier()
		obj = dgModifier.createNode( shaderName )
		dgModifier.doIt()
		builder = DummyBuilder()
		builder.build( obj, dummyClassName, basePath )
		dgModifier.deleteNode(obj)
		dgModifier.doIt()

	with open( os.path.join( basePath, 'register.py' ), 'w' ) as fhdl:
		fhdl.write('import maya.OpenMaya as OpenMaya\n')
		fhdl.write('import sys\n')
		for shaderName, dummyClassName in createShaders:
			fhdl.write('from %s import *\n' % dummyClassName )

		fhdl.write('def registerAll(mplugin):\n')
		for shaderName, dummyClassName in createShaders:
			addRegisterCmd(fhdl, dummyClassName)

		fhdl.write('def deregisterAll(mplugin):\n')
		for shaderName, dummyClassName in createShaders:
			addDeregisterCmd(fhdl, dummyClassName)

