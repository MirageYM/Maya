-- premake5.lua
-- Maya C++ plugin

---------------------------------------------------------------------
-- options
newoption{
	trigger = "mayalocation",
	value = "PATH",
	description = "Maya DevKit path"
}

newoption{
	trigger = "mayaversion",
	description = "Maya version id"
}

newoption{
	trigger = "dxsdk",
	value = "PATH",
	description = "DirectX SDK path"
}

newoption{
	trigger = "platform",
	description = "platform version"
}



---------------------------------------------------------------------
-- Maya lib
mayaLib = {
	'Foundation',
	'OpenMaya',
	'OpenMayaRender',
	'OpenMayaAnim',
	'OpenMayaUI'
}

--dxsdk lib
dxsdkLib = {
	'd3dx11.lib'
}


---------------------------------------------------------------------
-- project setting
projectSuffix = ""
mayaVersionStr = ""
pluginBaseName = "DX11CurvatureViewPort"

if _OPTIONS["mayaversion"] then
	projectSuffix = _OPTIONS["mayaversion"]
	str = tostring( _OPTIONS["mayaversion"] )

	if string.find( str, '%.' ) then
		mayaVersionStr = string.gsub( str, "%.", "" )
	else
		mayaVersionStr = str .. "0"
	end
end


---------------------------------------------------------------------
-- solution
solutionName = pluginBaseName .. projectSuffix
solution( solutionName )
	configurations { "Debug", "Release" }

	if _OPTIONS["platform"] then
		platforms{ _OPTIONS["platform" ] }
	else
		platforms{ "native", "x64", "x86" }
	end
	
	---------------------------------------------------------------------
	-- solution
	projectName = pluginBaseName .. projectSuffix
	project( projectName )
		kind "SharedLib"
		language "C++"

		mayaIncludePath = "\"" .. _OPTIONS[ 'mayalocation' ] .. "/include" .. "\""
		mayaLibPath = "\"" .. _OPTIONS[ 'mayalocation' ] .. "/lib" .. "\""
		dxsdkIncludePath = "\"" .. _OPTIONS[ 'dxsdk' ] .. "/include" .. "\""
		dxsdkLibPath = "\"" .. _OPTIONS[ 'dxsdk' ] .. "/lib/" .. _OPTIONS[ 'platform' ] .. "\""
		
		--Add all srcs
		thisPluginSrcs = {
			"**.hpp",
			"**.cpp"
		}
		
		files {
			thisPluginSrcs
		}
		
		includedirs{
			mayaIncludePath,
			dxsdkIncludePath
		}

		libdirs{
			mayaLibPath,
			dxsdkLibPath
		}
			
		links{
			mayaLib,
			dxsdkLib
		}

		--setting up output directory for multiple version delpoyment.
		if not _OPTIONS["mayaversion"] then
			targetdir "%{prj.location}/%{cfg.architecture}/%{cfg.buildcfg}"
			objdir "%{prj.location}/%{cfg.architecture}/%{cfg.buildcfg}/obj"
		else
			targetdir "%{prj.location}/maya%{_OPTIONS[\"mayaversion\"]}/%{cfg.architecture}/%{cfg.buildcfg}"
			objdir "%{prj.location}/maya%{_OPTIONS[\"mayaversion\"]}/%{cfg.architecture}/%{cfg.buildcfg}/obj"
		end
		
		--target setup
		targetname( pluginBaseName )
		implibextension ".lib"
		targetextension ".mll"

		--configuration specific 
		configuration "windows"
			mayaDefineVerStr = "MAYA_VERSION=" .. mayaVersionStr
			if not _OPTIONS["mayaversion"] then
				defines{ 'REQUIRE_IOSTREAM', '_BOOL', '_CRT_SECURE_NO_WARNINGS', 'NT_PLUGIN' }
			elseif tonumber( _OPTIONS["mayaversion"] ) >= 2016 then
				defines{ 'REQUIRE_IOSTREAM', '_BOOL', '_CRT_SECURE_NO_WARNINGS', 'NT_PLUGIN', 'SDK_HAS_MGL_', mayaDefineVerStr }
			else
				defines{ 'REQUIRE_IOSTREAM', '_BOOL', '_CRT_SECURE_NO_WARNINGS', 'NT_PLUGIN', mayaDefineVerStr }
			end

		configuration "Debug"
			defines { "DEBUG" }
			flags { "Symbols" }

		configuration "Release"
			defines { "NDEBUG" }
			optimize "On"
		
