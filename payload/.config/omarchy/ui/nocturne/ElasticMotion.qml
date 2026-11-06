import QtQuick

// Shared surface motion. Opening has a small elastic settle; closing is
// critically damped so a hidden surface cannot rebound into view.
Item {
  id: root
  property bool active: false
  property bool ready: true
  property bool reduced: false
  property real closedWidth: 0.86
  property real closedHeight: 0.9
  property real progress: 0
  readonly property real widthFactor: closedWidth + (1 - closedWidth) * progress
  readonly property real heightFactor: closedHeight + (1 - closedHeight) * progress
  readonly property real alpha: Math.max(0, Math.min(1, progress * 1.7))

  // Set the physical parameters before retargeting. Separate property
  // bindings can otherwise start the exit with the previous entry values.
  function retarget() {
    springMotion.damping = active ? 0.36 : 0.34
    springMotion.mass = active ? 1 : 0.45
    springMotion.epsilon = active ? 0.02 : 0.05
    progress = active && ready ? 1 : 0
  }
  onActiveChanged: retarget()
  onReadyChanged: retarget()
  Component.onCompleted: retarget()

  Behavior on progress {
    enabled: !root.reduced
    SpringAnimation {
      id: springMotion
      spring: 5
      damping: 0.36
      mass: 1
      epsilon: 0.02
    }
  }
}
