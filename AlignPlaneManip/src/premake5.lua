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


---------------------------------------------------------------------
-- project setting
projectSuffix = ""
pluginBaseName = "AlignPlaneManip"

if _OPTIONS["mayaversion"] then
	projectSuffix = _OPTIONS["mayaversion"]
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
		
		--Add all srcs
		thisPluginSrcs = {
			"**.hpp",
			"**.cpp"
		}
		
		files {
			thisPluginSrcs
		}
		
		includedirs{
			mayaIncludePath
		}

		libdirs{
			mayaLibPath
		}
			
		links{
			mayaLib
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
			if not _OPTIONS["mayaversion"] then
				defines{ 'REQUIRE_IOSTREAM', '_BOOL', '_CRT_SECURE_NO_WARNINGS', 'NT_PLUGIN' }
			elseif tonumber( _OPTIONS["mayaversion"] ) >= 2016 then
				defines{ 'REQUIRE_IOSTREAM', '_BOOL', '_CRT_SECURE_NO_WARNINGS', 'NT_PLUGIN', 'SDK_HAS_MGL_' }
			else
				defines{ 'REQUIRE_IOSTREAM', '_BOOL', '_CRT_SECURE_NO_WARNINGS', 'NT_PLUGIN' }
			end

		configuration "Debug"
			defines { "DEBUG" }
			flags { "Symbols" }

		configuration "Release"
			defines { "NDEBUG" }
			optimize "On"
		
