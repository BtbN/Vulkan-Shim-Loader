#!/usr/bin/env python3
import os
import re
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) > 1:
    sys.stdout = open(sys.argv[1], "w")

os.chdir(os.path.dirname(__file__))

# Don't forget to fetch the submodule.
vkxml = "Vulkan-Headers/registry/vk.xml"

commands = []
for cmd in ET.parse(vkxml).getroot().findall(".//commands/command"):
    proto = cmd.find("proto")
    if proto is None:
        continue
    if "vulkan" not in cmd.get("export", "").lower().split(","):
        continue

    name = proto.find("name").text
    # The XML is weird, stuff like "const" or "*" Are outside of the <type> tags.
    ret_type = "".join(proto.itertext()).strip().rsplit(" ", 1)[0]
    params = []
    param_names = []
    for p in cmd.findall("param"):
        params.append(re.sub(r"\s+", " ", "".join(p.itertext()).strip()))
        param_names.append(p.find("name").text)

    commands.append((ret_type, name, params, param_names))


print("""// Auto-Generated from vk.xml
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
""")

for ret_type, name, params, param_names in commands:
    print(f"static PFN_{name} ptr_{name} = NULL;")

print("""
#ifdef _WIN32
static HMODULE vklib = NULL;
#else
static void *vklib = NULL;
#endif

__attribute__((destructor))
static void deinit() {
#ifdef _WIN32
    FreeLibrary(vklib);
#else
    dlclose(vklib);
#endif
    vklib = NULL;
}

__attribute__((constructor))
static void init() {
#ifdef _WIN32
    vklib = LoadLibraryExA("vulkan-1.dll", NULL, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
#define dlsym GetProcAddress
#else
    vklib = dlopen("libvulkan.so.1", RTLD_LAZY | RTLD_LOCAL);
#endif

    if (!vklib)
        return;
""")

for ret_type, name, params, param_names in commands:
    print(f'    ptr_{name} = (PFN_{name})dlsym(vklib, "{name}");')

print("""
#ifdef _WIN32
#undef dlsym
#endif
}
""")

for ret_type, name, params, param_names in commands:
    decl_params = ", ".join(params) if params else "void"
    args = ", ".join(param_names) if param_names else ""

    print(f"{ret_type} VKAPI_CALL {name}({decl_params}) {{")

    print(f"    if (likely(ptr_{name})) {{")
    if ret_type == "void":
        print(f"        ptr_{name}({args});")
    else:
        print(f"        return ptr_{name}({args});")
    print(f"    }}")

    if ret_type == "VkResult":
        print(f"    return VK_ERROR_INITIALIZATION_FAILED;")
    elif ret_type.endswith("*"):
        print(f"    return NULL;")
    elif ret_type != "void":
        print(f"    return ({ret_type})0;")
    print(f"}}")
    print(f"")
