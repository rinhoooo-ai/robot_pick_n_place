#!/bin/bash
# =============================================================================
# setup.sh — Robot Pick and Place | ROS2 Jazzy + Gazebo Harmonic + MoveIt2
# =============================================================================
# Usage:
#   bash scripts/setup.sh
#
# What this does:
#   1. Check system requirements
#   2. Install ROS2 Jazzy (if not installed)
#   3. Install all ROS2 dependencies (Gazebo, MoveIt2, controllers, etc.)
#   4. Install Python dependencies (OpenCV, numpy)
#   5. Install Franka-related packages
#   6. Build the workspace with colcon
#   7. Add source to ~/.bashrc
# =============================================================================

set -e  # exit on any error

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step()    { echo -e "\n${BOLD}━━━ $1 ━━━${NC}"; }

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WS_DIR="$REPO_DIR/ros2_ws"

echo ""
echo -e "${BOLD}🦾 Robot Pick and Place — Setup Script${NC}"
echo -e "   Repo : $REPO_DIR"
echo -e "   WS   : $WS_DIR"
echo ""

# =============================================================================
# STEP 1 — System check
# =============================================================================
step "1/7  System check"

OS=$(lsb_release -cs 2>/dev/null || echo "unknown")
if [[ "$OS" != "noble" ]]; then
  warn "Expected Ubuntu 24.04 (noble), got '$OS'. Proceeding anyway..."
else
  success "Ubuntu 24.04 detected"
fi

ARCH=$(uname -m)
if [[ "$ARCH" != "x86_64" && "$ARCH" != "aarch64" ]]; then
  error "Unsupported architecture: $ARCH"
fi
success "Architecture: $ARCH"

# =============================================================================
# STEP 2 — ROS2 Jazzy
# =============================================================================
step "2/7  ROS2 Jazzy"

if source /opt/ros/jazzy/setup.bash 2>/dev/null; then
  success "ROS2 Jazzy already installed"
else
  info "Installing ROS2 Jazzy..."

  sudo apt update && sudo apt install -y curl gnupg lsb-release

  sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

  sudo apt update
  sudo apt install -y ros-jazzy-desktop python3-rosdep python3-colcon-common-extensions

  source /opt/ros/jazzy/setup.bash
  success "ROS2 Jazzy installed"
fi

# =============================================================================
# STEP 3 — ROS2 dependencies (Gazebo, MoveIt2, controllers)
# =============================================================================
step "3/7  ROS2 packages"

sudo apt update

PACKAGES=(
  # Gazebo Harmonic + ROS2 bridge
  ros-jazzy-ros-gz
  ros-jazzy-ros-gz-sim
  ros-jazzy-ros-gz-bridge
  ros-jazzy-ros-gz-interfaces

  # MoveIt2
  ros-jazzy-moveit
  ros-jazzy-moveit-ros-planning-interface
  ros-jazzy-moveit-ros-move-group

  # ros2_control + controllers
  ros-jazzy-ros2-control
  ros-jazzy-ros2-controllers
  ros-jazzy-joint-state-broadcaster
  ros-jazzy-joint-trajectory-controller
  ros-jazzy-gripper-controllers

  # Robot state + TF
  ros-jazzy-robot-state-publisher
  ros-jazzy-joint-state-publisher
  ros-jazzy-joint-state-publisher-gui
  ros-jazzy-xacro
  ros-jazzy-tf2-ros
  ros-jazzy-tf2-tools

  # Camera / vision
  ros-jazzy-cv-bridge
  ros-jazzy-image-transport

  # Franka
  ros-jazzy-franka-description
  ros-jazzy-franka-msgs
)

info "Installing ${#PACKAGES[@]} ROS2 packages..."
sudo apt install -y "${PACKAGES[@]}"
success "ROS2 packages installed"

# =============================================================================
# STEP 4 — Python dependencies
# =============================================================================
step "4/7  Python dependencies"

pip install --upgrade pip
pip install \
  opencv-python \
  numpy \
  transforms3d

success "Python dependencies installed"

# =============================================================================
# STEP 5 — rosdep
# =============================================================================
step "5/7  rosdep"

if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  info "Initializing rosdep..."
  sudo rosdep init
fi

info "Updating rosdep..."
rosdep update

info "Installing workspace dependencies..."
cd "$WS_DIR"
rosdep install --from-paths src --ignore-src -r -y
success "rosdep done"

# =============================================================================
# STEP 6 — Build workspace
# =============================================================================
step "6/7  Build workspace"

cd "$WS_DIR"
info "Running colcon build..."

colcon build \
  --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_cohesion+

success "Build complete"

# =============================================================================
# STEP 7 — Source setup in ~/.bashrc
# =============================================================================
step "7/7  Shell setup"

ROS_SOURCE="source /opt/ros/jazzy/setup.bash"
WS_SOURCE="source $WS_DIR/install/setup.bash"
GZ_MODEL="export GZ_SIM_RESOURCE_PATH=$WS_DIR/src/pick_n_place_gazebo/models"

add_to_bashrc() {
  local line="$1"
  local label="$2"
  if grep -qF "$line" ~/.bashrc; then
    warn "$label already in ~/.bashrc — skipping"
  else
    echo "$line" >> ~/.bashrc
    success "Added $label to ~/.bashrc"
  fi
}

add_to_bashrc "$ROS_SOURCE" "ROS2 Jazzy source"
add_to_bashrc "$WS_SOURCE"  "workspace source"
add_to_bashrc "$GZ_MODEL"   "Gazebo model path"

# =============================================================================
# Done!
# =============================================================================
echo ""
echo -e "${GREEN}${BOLD}✅  Setup complete!${NC}"
echo ""
echo -e "   Activate in your current terminal:"
echo -e "   ${BOLD}source ~/.bashrc${NC}"
echo ""
echo -e "   Then launch the simulation:"
echo -e "   ${BOLD}ros2 launch pick_n_place_gazebo simulation.launch.py${NC}"
echo ""
