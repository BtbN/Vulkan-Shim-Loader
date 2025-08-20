cmake_minimum_required(VERSION 3.16)
project(VulkanShimLoader C)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
set(GENERATED_LOADER ${CMAKE_CURRENT_BINARY_DIR}/loader.c)
add_custom_command(
  OUTPUT ${GENERATED_LOADER}
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/gen_shim.py ${GENERATED_LOADER}
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/gen_shim.py ${CMAKE_CURRENT_SOURCE_DIR}/Vulkan-Headers/registry/vk.xml
  VERBATIM
)

add_library(vulkan-shim STATIC ${GENERATED_LOADER})
set_target_properties(vulkan-shim PROPERTIES OUTPUT_NAME "vulkan-shim")
target_include_directories(vulkan-shim PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/Vulkan-Headers/include)

include(GNUInstallDirs)
install(TARGETS vulkan-shim
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
