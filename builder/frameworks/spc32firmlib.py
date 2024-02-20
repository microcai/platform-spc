import sys
from os.path import exists,isdir, isfile, join
from string import Template

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()
mcu = board.get("build.mcu", "")
product_line = board.get("build.product_line", "")
bsp = board.get("build.bsp", "")

env.SConscript("_bare.py")

FRAMEWORK_DIR = platform.get_package_dir("framework-spc32firmlib")
assert isdir(FRAMEWORK_DIR)

FRAMEWORK_LIB_DIR = join(FRAMEWORK_DIR, bsp + "_FW", "Libraries")
assert isdir(FRAMEWORK_LIB_DIR)

FRAMEWORK_MIDDLEWARE_DIR = join(FRAMEWORK_DIR, bsp + "_Firmware_Library", "middlewares")



def get_linker_script():
    ldscript = join(FRAMEWORK_LIB_DIR, "CMSIS", "device", "startup", "gcc",
                    "linker", product_line + "_FLASH.ld")

    if isfile(ldscript):
        return ldscript

    sys.stderr.write("Warning! Cannot find a linker script for the required board! "+ldscript)


env.Append(
    CPPPATH=[
        join(FRAMEWORK_LIB_DIR, "CMSIS", "cm3"),
        join(FRAMEWORK_LIB_DIR, "CMSIS", "device"),
        join(FRAMEWORK_LIB_DIR, "drivers", "inc"),
        join(FRAMEWORK_LIB_DIR, "drivers", "inc", "reg"),
        join(FRAMEWORK_LIB_DIR, "drivers", "inc", "reg"),
        join(FRAMEWORK_DIR, "Utilities")
    ]
)

env.Append(
    CPPDEFINES=[
        "USE_STDPERIPH_DRIVER"
    ]
)

env.Append(
    CPPDEFINES=[
        env["BUILD_TYPE"].upper()
    ]
)

if not board.get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH=get_linker_script())

#
# Target: Build Firmware Library
#

extra_flags = board.get("build.extra_flags", "")

libs = []

libs.append(env.BuildLibrary(
    join("$BUILD_DIR", "CMSIS"),
    join(FRAMEWORK_LIB_DIR, "CMSIS", "cm3"),
    join(FRAMEWORK_LIB_DIR, "CMSIS", "device"),
    join(FRAMEWORK_LIB_DIR, "drivers", "src"),
    join(FRAMEWORK_DIR, "Utilities"),
    src_filter=[
        "+<*.c>",
        "+<startup/arm/startup_spc1068.c>"
    ]
))

middlewares = env.GetProjectOption("middlewares","")
if(middlewares):
    for x in middlewares.split(","):
        print("Middleware %s referenced." % x)
        if isdir(join(FRAMEWORK_MIDDLEWARE_DIR, x.strip())) and exists(join(FRAMEWORK_MIDDLEWARE_DIR, x.strip())):
            if x == "i2c_application_library": 
                env.Append(
                    CPPPATH=[
                        join(FRAMEWORK_MIDDLEWARE_DIR, x.strip())
                    ]
                )
                libs.append(env.BuildLibrary(
                    join("$BUILD_DIR", "middleware", x.strip()),
                    join(FRAMEWORK_MIDDLEWARE_DIR, x.strip()),
                    src_filter=["+<*.c>"]
                ))
            if x == "freertos":
                env.Append(
                    CPPPATH=[
                        join(FRAMEWORK_MIDDLEWARE_DIR, x.strip(), "source", "include"),
                        join(FRAMEWORK_MIDDLEWARE_DIR, x.strip(), "source", "portable", "GCC", "ARM_CM3")
                    ]
                )
                libs.append(env.BuildLibrary(
                    join("$BUILD_DIR", "middleware", x.strip()),
                    join(FRAMEWORK_MIDDLEWARE_DIR, x.strip(), "source"),
                    src_filter=[
                        "+<*.c>",
                        "+<portable/common/*.c>",
                        "+<portable/gcc/ARM_CM3/*.c>"
                    ]
                ))
        else:
            sys.stderr.write("Middleware %s not exist.\r\n" % x)

env.Append(LIBS=libs)
