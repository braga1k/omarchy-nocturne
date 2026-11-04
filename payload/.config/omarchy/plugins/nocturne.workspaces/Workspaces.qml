import QtQuick
import QtQuick.Layouts
import Quickshell.Hyprland
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "omarchy.workspaces"

  function workspaceById(id) {
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) {
      if (values[i].id === id) return values[i]
    }

    return null
  }

  function workspaceIds() {
    var ids = [1, 2, 3, 4, 5]
    var values = Hyprland.workspaces.values

    for (var i = 0; i < values.length; i++) {
      var id = values[i].id
      if (id > 0 && id <= 10 && ids.indexOf(id) === -1) ids.push(id)
    }

    ids.sort(function(left, right) { return left - right })
    return ids
  }

  function focusWorkspace(id) {
    if (!root.bar) return
    root.bar.run("hyprctl dispatch " + Util.shellQuote("hl.dsp.focus({ workspace = \"" + id + "\" })"))
  }

  readonly property real trailingGap: root.vertical ? 0 : Style.spaceReal(1.5)

  implicitWidth: grid.implicitWidth + trailingGap
  implicitHeight: grid.implicitHeight

  GridLayout {
    id: grid
    anchors.fill: parent
    anchors.rightMargin: root.trailingGap
    columns: root.vertical ? 1 : root.workspaceIds().length
    columnSpacing: root.vertical ? 0 : Style.space(1)
    rowSpacing: root.vertical ? Style.space(2) : 0

    Repeater {
      model: root.workspaceIds()

      WidgetButton {
        id: workspaceButton
        required property int modelData

        readonly property var workspace: root.workspaceById(modelData)
        readonly property bool occupied: workspace !== null && workspace.toplevels.values.length > 0
        readonly property bool focused: Hyprland.focusedWorkspace !== null && Hyprland.focusedWorkspace.id === modelData

        bar: root.bar
        text: modelData === 10 ? "0" : String(modelData)
        // O texto e a cápsula de foco mudam no mesmo frame. O label nativo
        // interpola a cor, o que reduz o contraste durante esta inversão.
        labelVisible: false
        foreground: focused ? Color.background : (occupied ? Color.foreground : Util.alpha(Color.foreground, 0.72))
        horizontalMargin: 6
        verticalPadding: 6
        fixedWidth: root.vertical ? root.barSize : Style.space(26)
        fixedHeight: root.barSize
        tooltipText: "Workspace " + modelData

        Rectangle {
          z: -1
          anchors.centerIn: parent
          width: parent.width - 2
          height: parent.height - 6
          radius: Math.min(7, height / 2)
          color: workspaceButton.focused ? Color.accent : "transparent"

          Rectangle {
            anchors.fill: parent
            radius: parent.radius
            color: Style.hoverFill
            visible: !workspaceButton.focused
            opacity: workspaceButton.tooltipHovered ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
          }
        }

        Text {
          anchors.centerIn: parent
          text: workspaceButton.text
          color: workspaceButton.foreground
          font.family: workspaceButton.fontFamily
          font.pixelSize: workspaceButton.fontSize
          renderType: Text.NativeRendering
        }

        Rectangle {
          anchors.horizontalCenter: parent.horizontalCenter
          anchors.bottom: parent.bottom
          anchors.bottomMargin: 2
          width: 3
          height: 2
          radius: 1
          color: Color.accent
          visible: workspaceButton.occupied && !workspaceButton.focused
        }

        onPressed: function() { root.focusWorkspace(modelData) }
      }
    }
  }
}
