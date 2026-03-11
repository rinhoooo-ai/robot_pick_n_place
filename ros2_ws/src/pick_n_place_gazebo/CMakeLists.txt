cmake_minimum_required(VERSION 3.8)
project(pick_n_place_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# =============================
# Find dependencies
# =============================
find_package(ament_cmake REQUIRED)

# =============================
# Install folders (no compiled nodes — Python + config only)
# =============================
install(
  DIRECTORY
    launch
    worlds
    models
    config
    rviz
    scripts
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
