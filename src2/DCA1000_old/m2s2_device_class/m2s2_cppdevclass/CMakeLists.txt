cmake_minimum_required(VERSION 3.1.0)
project(m2s2_cppdevclass)

file(GLOB_RECURSE m2s2_cppdevclass_SRC
        ${CMAKE_SOURCE_DIR}/src/*.cpp)

file(GLOB_RECURSE m2s2_cppdevclass_HEADERS
        ${CMAKE_SOURCE_DIR}/include/*.hpp)

option(SERIAL_BUILD_SHARED_LIBS "Build m2s2_cppdevclass shared library" OFF)

if (SERIAL_BUILD_SHARED_LIBS)
  set(LibType SHARED)
else()
  set(LibType STATIC)
endif()

add_library(m2s2_cppdevclass ${LibType} ${m2s2_cppdevclass_SRC} ${m2s2_cppdevclass_HEADERS})


target_include_directories(m2s2_cppdevclass PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
                                                $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/${PROJECT_NAME}>)                                                  

# On Linux, "sudo make install" will typically copy the library
# into the folder /usr/local/bin
install(TARGETS m2s2_cppdevclass DESTINATION lib)

# On Linux, "sudo make install" will typically copy the
# folder into /usr/local/include
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/ DESTINATION include)