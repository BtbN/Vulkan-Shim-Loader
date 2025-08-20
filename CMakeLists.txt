cmake_minimum_required(VERSION 3.22.1)
project(VulkanShimLoader C)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

add_subdirectory(Vulkan-Headers)
get_directory_property(VK_VERSION_STRING DIRECTORY Vulkan-Headers DEFINITION VK_VERSION_STRING)
message(STATUS "Vulkan-Headers version: ${VK_VERSION_STRING}")

find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(GENERATED_LOADER "${CMAKE_CURRENT_BINARY_DIR}/loader.c")
add_custom_command(
  OUTPUT "${GENERATED_LOADER}"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/gen_shim.py" "${GENERATED_LOADER}"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/gen_shim.py" "${CMAKE_CURRENT_SOURCE_DIR}/Vulkan-Headers/registry/vk.xml"
  VERBATIM)

option(VULKAN_SHIM_IMPERSONATE "Impersonate the real Vulkan-Loader" OFF)
add_library(vulkan-shim STATIC "${GENERATED_LOADER}")

if(VULKAN_SHIM_IMPERSONATE)
  if(WIN32)
    set(VULKAN_SHIM_LIB_NAME vulkan-1)
  else()
    set(VULKAN_SHIM_LIB_NAME vulkan)
  endif()
else()
  set(VULKAN_SHIM_LIB_NAME vulkan-shim)
endif()
set_target_properties(vulkan-shim PROPERTIES
  OUTPUT_NAME "${VULKAN_SHIM_LIB_NAME}"
  VERSION "${VK_VERSION_STRING}")
target_include_directories(vulkan-shim PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/Vulkan-Headers/include")

if(VULKAN_SHIM_IMPERSONATE)
  set_target_properties(vulkan-shim PROPERTIES EXPORT_NAME Loader)
  add_library(Vulkan::Loader ALIAS vulkan-shim)

  install(TARGETS vulkan-shim
    EXPORT VulkanLoaderConfig
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}")
else()
  install(TARGETS vulkan-shim
    ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}")
endif()

set(VULKAN_SHIM_PKG_VERSION "${VK_VERSION_STRING}")
if(VULKAN_SHIM_IMPERSONATE)
  set(VULKAN_SHIM_PKG_LIBNAME vulkan)
else()
  set(VULKAN_SHIM_PKG_LIBNAME vulkan-shim)
endif()
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/vulkan-shim.pc.in"
               "${CMAKE_CURRENT_BINARY_DIR}/${VULKAN_SHIM_PKG_LIBNAME}.pc" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/${VULKAN_SHIM_PKG_LIBNAME}.pc"
        DESTINATION "${CMAKE_INSTALL_LIBDIR}/pkgconfig")

if (VULKAN_SHIM_IMPERSONATE)
  write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/VulkanLoaderConfigVersion.cmake"
    VERSION "${VK_VERSION_STRING}"
    COMPATIBILITY SameMajorVersion
  )
  install(EXPORT VulkanLoaderConfig
    NAMESPACE Vulkan::
    DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/VulkanLoader"
  )
  install(FILES "${CMAKE_CURRENT_BINARY_DIR}/VulkanLoaderConfigVersion.cmake"
          DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/VulkanLoader")
endif()
