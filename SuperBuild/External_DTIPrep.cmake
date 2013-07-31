# Make sure this file is included only once by creating globally unique varibles
# based on the name of this included file.
get_filename_component(CMAKE_CURRENT_LIST_FILENAME ${CMAKE_CURRENT_LIST_FILE} NAME_WE)
if(${CMAKE_CURRENT_LIST_FILENAME}_FILE_INCLUDED)
  return()
endif()
set(${CMAKE_CURRENT_LIST_FILENAME}_FILE_INCLUDED 1)

## External_${extProjName}.cmake files can be recurisvely included,
## and cmake variables are global, so when including sub projects it
## is important make the extProjName and proj variables
## appear to stay constant in one of these files.
## Store global variables before overwriting (then restore at end of this file.)
ProjectDependancyPush(CACHED_extProjName ${extProjName})
ProjectDependancyPush(CACHED_proj ${proj})

# Make sure that the ExtProjName/IntProjName variables are unique globally
# even if other External_${ExtProjName}.cmake files are sourced by
# SlicerMacroCheckExternalProjectDependency
set(extProjName DTIPrep) #The find_package known name
set(proj        ${extProjName}) #This local name
set(${extProjName}_REQUIRED_VERSION "")  #If a required version is necessary, then set this, else leave blank

#if(${USE_SYSTEM_${extProjName}})
#  unset(${extProjName}_DIR CACHE)
#endif()

# Sanity checks
if(DEFINED ${extProjName}_DIR AND NOT EXISTS ${${extProjName}_DIR})
  message(FATAL_ERROR "${extProjName}_DIR variable is defined but corresponds to non-existing directory (${${extProjName}_DIR})")
endif()

# Set dependency list
set(${proj}_DEPENDENCIES DCMTK ITKv4 SlicerExecutionModel VTK BRAINSTools ANTs)
#if(${PROJECT_NAME}_BUILD_DICOM_SUPPORT)
#  list(APPEND ${proj}_DEPENDENCIES DCMTK)
#endif()

# Include dependent projects if any
SlicerMacroCheckExternalProjectDependency(${proj})

if(NOT ( DEFINED "USE_SYSTEM_${extProjName}" AND "${USE_SYSTEM_${extProjName}}" ) )
  #message(STATUS "${__indent}Adding project ${proj}")

  # Set CMake OSX variable to pass down the external project
  set(CMAKE_OSX_EXTERNAL_PROJECT_ARGS)
  if(APPLE)
    list(APPEND CMAKE_OSX_EXTERNAL_PROJECT_ARGS
      -DCMAKE_OSX_ARCHITECTURES=${CMAKE_OSX_ARCHITECTURES}
      -DCMAKE_OSX_SYSROOT=${CMAKE_OSX_SYSROOT}
      -DCMAKE_OSX_DEPLOYMENT_TARGET=${CMAKE_OSX_DEPLOYMENT_TARGET})
  endif()

  set(BRAINSCommonLibWithANTs ON)
  if(BRAINSCommonLibWithANTs)
    set(BRAINSCommonLibWithANTs_OPTIONS
      -DBRAINSTools_SOURCE_DIR:PATH=${BRAINSTools_SOURCE_DIR}
      -DUSE_ANTs:BOOL=ON
      -DUSE_SYSTEM_ANTs:BOOL=ON
      -DANTs_SOURCE_DIR:PATH=${ANTs_SOURCE_DIR}
      -DANTs_LIBRARY_DIR:PATH=${ANTs_LIBRARY_DIR}
      -DUSE_SYSTEM_Boost:BOOL=ON
      -DBoost_NO_BOOST_CMAKE:BOOL=ON #Set Boost_NO_BOOST_CMAKE to ON to disable the search for boost-cmake
      -DBoost_DIR:PATH=${BOOST_ROOT}
      -DBOOST_ROOT:PATH=${BOOST_ROOT}
      -DBOOST_INCLUDE_DIR:PATH=${BOOST_INCLUDE_DIR}
      -DDTIPrepTools_SUPERBUILD:STRING=OFF
      )
  else()
    set(BRAINSCommonLibWithANTs_OPTIONS
      -DUSE_ANTs:BOOL=OFF)
  endif()

  ### --- Project specific additions here
  set(${proj}_CMAKE_OPTIONS
      -DCMAKE_INSTALL_PREFIX:PATH=${CMAKE_CURRENT_BINARY_DIR}/${proj}-install
      -DKWSYS_USE_MD5:BOOL=ON # Required by SlicerExecutionModel
      -DUSE_SYSTEM_ITK:BOOL=ON
      -DUSE_SYSTEM_VTK:BOOL=ON
      -DUSE_SYSTEM_DCMTK:BOOL=ON
      -DUSE_SYSTEM_SlicerExecutionModel:BOOL=ON
      -DITK_DIR:PATH=${ITK_DIR}
      -DVTK_DIR:PATH=${VTK_DIR}
      -DDCMTK_DIR:PATH=${DCMTK_DIR}
      -DGenerateCLP_DIR:PATH=${GenerateCLP_DIR}
      -DSlicerExecutionModel_DIR:PATH=${SlicerExecutionModel_DIR}
      -DBRAINSTools_SOURCE_DIR:PATH=${BRAINSTools_SOURCE_DIR}
      -DBRAINSCommonLib_DIR:PATH=${BRAINSCommonLib_DIR}
      -D${proj}_USE_QT:BOOL=${LOCAL_PROJECT_NAME}_USE_QT
      -D${proj}_SUPERBUILD:BOOL=OFF
      ${BRAINSCommonLibWithANTs_OPTIONS}
    )

  ### --- End Project specific additions
  set(${proj}_REPOSITORY https://www.nitrc.org/svn/dtiprep/trunk)
  ExternalProject_Add(${proj}
    SVN_REPOSITORY ${${proj}_REPOSITORY}
    SVN_REVISION -r "255"
    SVN_USERNAME slicerbot
    SVN_PASSWORD slicer
    SOURCE_DIR ${CMAKE_CURRENT_LIST_DIR}/ExternalSources/${proj}
    BINARY_DIR ${proj}-build
    INSTALL_COMMAND ""
    LOG_CONFIGURE 0  # Wrap configure in script to ignore log output from dashboards
    LOG_BUILD     0  # Wrap build in script to to ignore log output from dashboards
    LOG_TEST      0  # Wrap test in script to to ignore log output from dashboards
    LOG_INSTALL   0  # Wrap install in script to to ignore log output from dashboards
    ${cmakeversion_external_update} "${cmakeversion_external_update_value}"
    CMAKE_GENERATOR ${gen}
    CMAKE_ARGS
      ${CMAKE_OSX_EXTERNAL_PROJECT_ARGS}
      ${COMMON_EXTERNAL_PROJECT_ARGS}
      ${${proj}_CMAKE_OPTIONS}
## We really do want to install in order to limit # of include paths INSTALL_COMMAND ""
    DEPENDS
      ${${proj}_DEPENDENCIES}
  )
  set(${extProjName}_DIR ${CMAKE_BINARY_DIR}/${proj}-build)
else()
  if(${USE_SYSTEM_${extProjName}})
    find_package(${extProjName} ${${extProjName}_REQUIRED_VERSION} REQUIRED)
    message("USING the system ${extProjName}, set ${extProjName}_DIR=${${extProjName}_DIR}")
  endif()
  # The project is provided using ${extProjName}_DIR, nevertheless since other
  # project may depend on ${extProjName}, let's add an 'empty' one
  SlicerMacroEmptyExternalProject(${proj} "${${proj}_DEPENDENCIES}")
endif()

list(APPEND ${CMAKE_PROJECT_NAME}_SUPERBUILD_EP_VARS ${extProjName}_DIR:PATH)

ProjectDependancyPop(CACHED_extProjName extProjName)
ProjectDependancyPop(CACHED_proj proj)