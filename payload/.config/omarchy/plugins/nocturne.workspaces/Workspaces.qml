import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "omarchy.workspaces"

  // Follow per-monitor defaults or the explicit global-sequence preference.
  readonly property int slots: 10
  readonly property var monitor: {
    var window = root.QsWindow.window
    return window && window.screen ? Hyprland.monitorFor(window.screen) : Hyprland.focusedMonitor
  }
  readonly property string monitorName: monitor ? monitor.name : ""
  property var blocks: ({})
  readonly property bool perMonitor: root.setting("perMonitor", Object.keys(blocks).length > 0)
  readonly property int block: !perMonitor ? 0 : (blocks[monitorName] !== undefined ? blocks[monitorName] : Math.max(0, blockOf(activeWorkspaceId())))
  function readBlocks(text) {
    var next = {}
    String(text || "").split("\n").forEach(function(line) {
      var fields = line.split("\t"), block = Number(fields[0])
      if (fields.length >= 3 && fields[1] && Number.isInteger(block) && block >= 0) next[fields[1]] = block
    })
    root.blocks = next
  }
  FileView {
    path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/omarchy/monitor-workspaces"
    watchChanges: true; printErrors: false
    onLoaded: root.readBlocks(text())
    onFileChanged: reload()
    onLoadFailed: root.readBlocks("")
  }
  function blockOf(id) { return Math.floor((id - 1) / root.slots) }
  function slotOf(id) { return (id - 1) % root.slots + 1 }
  function labelOf(id) {
    var number = root.perMonitor ? root.slotOf(id) : id
    return number === 10 ? "0" : String(number)
  }
  function activeWorkspaceId() {
    var active = perMonitor ? (root.monitor ? root.monitor.activeWorkspace : null) : Hyprland.focusedWorkspace
    return active ? active.id : -1
  }
  function workspaceById(id) {
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) if (values[i].id === id) return values[i]
    return null
  }
  function workspaceIds() {
    var base = root.block * root.slots
    var ids = [base+1,base+2,base+3,base+4,base+5], guests = []
    var values = Hyprland.workspaces.values
    for (var i = 0; i < values.length; i++) {
      var id = values[i].id
      if (id <= 0) continue
      if (!root.perMonitor || root.blockOf(id) === root.block) {
        if (ids.indexOf(id) === -1) ids.push(id)
      } else if (root.perMonitor && values[i].monitor && values[i].monitor.name === root.monitorName) guests.push(id)
    }
    ids.sort(function(a,b) {return a-b});guests.sort(function(a,b) {return a-b})
    return ids.concat(guests)
  }
  function focusWorkspace(id) {
    if (!root.bar) return
    var expression = root.perMonitor && root.blockOf(id) === root.block
      ? "o.workspaces.focus(" + root.slotOf(id) + ", " + JSON.stringify(root.monitorName) + ")"
      : "hl.dsp.focus({ workspace = \"" + id + "\" })"
    root.bar.run("hyprctl dispatch " + Util.shellQuote(expression))
  }
  Connections {
    target: Hyprland
    function onRawEvent(event) {
      var name = event ? String(event.name) : ""
      if ((name === "workspacev2" && root.monitor && root.monitor.focused)
          || name === "moveworkspacev2" || name === "changeworkspaceid" || name === "configreloaded") {
        Hyprland.refreshMonitors(); Hyprland.refreshWorkspaces()
      }
    }
  }
  ShellIpc {
    target: "nocturne.workspaces." + root.monitorName
    function inspect(): string {
      var window=root.QsWindow.window, screen=window ? window.screen : null, buttons=[]
      for(var i=0;i<workspaceRepeater.count;i++) {
        var button=workspaceRepeater.itemAt(i)
        if (!button || !window || !screen) continue
        var p=button.mapToItem(window.contentItem,button.width/2,button.height/2)
        buttons.push({id:button.modelData,label:button.text,focused:button.focused,occupied:button.occupied,
          x:screen.x+p.x,y:screen.y+p.y})
      }
      return JSON.stringify({monitor:root.monitorName,block:root.block,perMonitor:root.perMonitor,active:root.activeWorkspaceId(),buttons:buttons})
    }
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
      id: workspaceRepeater
      model: root.workspaceIds()

      WidgetButton {
        id: workspaceButton
        required property int modelData

        readonly property var workspace: root.workspaceById(modelData)
        readonly property bool occupied: workspace !== null && workspace.toplevels.values.length > 0
        readonly property bool focused: root.activeWorkspaceId() === modelData

        bar: root.bar
        text: root.labelOf(modelData)
        // O texto e a cápsula de foco mudam no mesmo frame. O label nativo
        // interpola a cor, o que reduz o contraste durante esta inversão.
        labelVisible: false
        foreground: focused ? Color.background : (occupied ? Color.foreground : Util.alpha(Color.foreground, 0.72))
        horizontalMargin: 6
        verticalPadding: 6
        fixedWidth: root.vertical ? root.barSize : Style.space(26)
        fixedHeight: root.barSize
        tooltipText: "Workspace " + (root.perMonitor ? root.slotOf(modelData) : modelData) + (root.perMonitor ? " · " + root.monitorName : "")

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
