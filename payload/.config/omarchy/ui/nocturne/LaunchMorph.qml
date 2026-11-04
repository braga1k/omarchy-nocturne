import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Widgets

// A visual bridge only. The native AppLibrary still owns desktop-entry launch.
Item {
  id: root
  property var appLibrary: null
  property bool active: false
  property bool presented: false
  property bool captureReady: false
  property var readyOutputs: ({})
  property var captureOutputs: ({})
  onPresentedChanged: if (presented) captured()
  property string phase: "idle"
  property string token: ""
  property string appId: ""
  property string label: ""
  property string icon: ""
  property int feedbackSerial: -1
  property var sourceVisual: ({labelX:50,labelY:20,labelWidth:240,iconX:13,iconY:17,iconSize:26,detail:"",detailY:0,detailSize:12})
  property string fontFamily: ""
  property int fontSize: 18
  property color foreground: "#e8e4ff"
  property color surface: "#302e49"
  property color edge: "#aba7eb"
  property real startRadius: 10
  property real endRadius: 18
  property real nativeBorder: 2
  property real nativePower: 2
  property real nativeAngle: 0
  property color nativeFirst: edge
  property color nativeLast: edge
  readonly property real decorationMix: Math.max(0, Math.min(1, (progress - 0.15) / 0.7))
  function mixColor(a,b,t) { return Qt.rgba(a.r+(b.r-a.r)*t,a.g+(b.g-a.g)*t,a.b+(b.b-a.b)*t,a.a+(b.a-a.a)*t) }
  property rect origin: Qt.rect(0,0,1,1)
  property rect destination: origin
  property string address: ""
  property var target: null
  property real progress: 0
  property real velocity: 0
  property real alpha: 1
  property real age: 0
  property double lastTick: 0
  property int sourceIndex: -1
  property var toplevels: Hyprland.toplevels.values
  property var waylandToplevels: ToplevelManager.toplevels.values
  readonly property real shapeProgress: Math.max(0, Math.min(1.04, progress))
  readonly property rect geometry: Qt.rect(
    origin.x + (destination.x-origin.x)*shapeProgress,
    origin.y + (destination.y-origin.y)*shapeProgress,
    Math.max(1, origin.width+(destination.width-origin.width)*shapeProgress),
    Math.max(1, origin.height+(destination.height-origin.height)*shapeProgress))

  function intersects(rect, screen) {
    return rect.x < screen.x+screen.width && rect.x+rect.width > screen.x
      && rect.y < screen.y+screen.height && rect.y+rect.height > screen.y
  }
  function outputsReady(rect, ready) {
    var outputs = Quickshell.screens.filter(screen => intersects(rect, screen))
    return outputs.length > 0 && outputs.every(screen => !!ready[screen.name])
  }
  function markOutputReady(name, copyReady) {
    var previous = copyReady ? captureOutputs : readyOutputs
    var next = Object.assign({}, previous); next[name] = true
    if (copyReady) captureOutputs = next
    else readyOutputs = next
    presented = outputsReady(origin, readyOutputs)
    captureReady = outputsReady(origin, captureOutputs) && outputsReady(destination, captureOutputs)
    captured()
  }

  function quote(value) {
    // Lua decimal escapes handle controls; JSON Unicode escapes are not Lua syntax.
    return "\"" + String(value).replace(/[\\"\x00-\x1f\x7f]/g, function(c) {
      return "\\" + ("00" + c.charCodeAt(0)).slice(-3)
    }) + "\""
  }
  function command(body) { return ["hyprctl", "repl", "if nocturneLaunch then " + body + " else return 'unavailable' end"] }
  function cancelTicket(ticket) {
    if (ticket) Quickshell.execDetached(command("return nocturneLaunch.cancel("+quote(ticket)+")"))
  }
  function launchNative(request) {
    if (!request || request.launched) return
    request.launched = true
    if (appLibrary) {
      appLibrary.launch(request.id, request.label)
      if (request.ticket === token) feedbackSerial = appLibrary.launchSerial
    }
  }
  function completeArm(ticket, request, result) {
    // Completion belongs to its process, never to a later UI request.
    if (ticket !== token || !active) {
      cancelTicket(ticket)
      launchNative(request)
      return
    }
    launchNative(request)
    if (result.trim() !== "armed") { cancel(); return }
    phase = "waiting"
    Hyprland.refreshToplevels()
  }
  function start(id, name, iconSource, rect, index, visual) {
    // UI input cannot queue a second launch while arming the first request.
    if (arm.running || arm.pendingRequest || !appLibrary) return false
    cancel()
    if (visual) sourceVisual = visual
    appId = id; label = name; icon = iconSource; origin = rect; destination = rect
    sourceIndex = index; address = ""; target = null
    progress = 0; velocity = 0; alpha = 1; age = 0
    token = Date.now().toString(36) + "-" + Math.floor(Math.random()*1e8).toString(36)
    var request = {id:id,label:name,ticket:token,launched:false}
    var entry = DesktopEntries.byId(id)
    var classes = [id]
    if (entry && entry.startupClass) classes.push(entry.startupClass)
    // Terminal desktop entries open a terminal, not a uniquely identifiable app.
    if (entry && entry.runInTerminal) { launchNative(request); return true }
    active = true; phase = "arming"
    arm.ticket = token
    arm.pendingRequest = request
    arm.command = command("return nocturneLaunch.arm("+quote(token)+",{"+classes.map(quote).join(",")+"})")
    arm.running = true
    timeout.restart()
    return true
  }
  function cancel() {
    cancelTicket(token)
    phase = "idle"; active = false; timeout.stop(); settle.stop(); animation.stop(); fadeOut.stop()
    presented = false; captureReady = false; readyOutputs = ({}); captureOutputs = ({})
    target = null; address = ""; sourceIndex = -1
  }
  function finish() {
    if (appLibrary && typeof appLibrary.closeLaunchFeedback === "function")
      appLibrary.closeLaunchFeedback(feedbackSerial)
    cancel()
  }
  function consumeStatus(value) {
    if (!active || phase === "arming" || phase === "handoff") return
    var fields = value.trim().split("\t")
    if (fields[0] === "held" && fields.length >= 6) {
      address = fields[1]
      if (fields.length >= 12) {
        nativeBorder = Math.max(0, Number(fields[6])); endRadius = Math.max(0, Number(fields[7]))
        nativePower = Math.max(2, Number(fields[8])); nativeAngle = Number(fields[11])
        nativeFirst = fields[9]; nativeLast = fields[10]
      }
      var rect = Qt.rect(Number(fields[2]),Number(fields[3]),Number(fields[4]),Number(fields[5]))
      if (!isFinite(rect.x+rect.y+rect.width+rect.height) || rect.width < 2 || rect.height < 2) { cancel(); return }
      if (phase === "waiting") { destination = rect; phase = "capturing" }
      else if (Math.abs(destination.x-rect.x)+Math.abs(destination.y-rect.y)+Math.abs(destination.width-rect.width)+Math.abs(destination.height-rect.height)>2) {
        // Abort an external layout change instead of distorting or misplacing the client.
        cancel(); return
      }
      var candidate = toplevels.find(w => w.address.replace(/^0x/, "") === address.replace(/^0x/, ""))
      if (candidate && candidate.wayland) target = candidate.wayland
      else Hyprland.refreshToplevels()
    } else if (fields[0] !== "armed") cancel()
  }
  function captured() {
    if (phase !== "capturing" || !presented || !captureReady || !outputsReady(destination, readyOutputs)) return
    phase = "moving"; lastTick = Date.now(); age = 0; animation.start()
  }
  function reveal() {
    if (phase !== "moving") return
    progress = 1; phase = "handoff"
    handoff.ticket = token
    handoff.command = command("return nocturneLaunch.reveal("+quote(token)+")")
    handoff.running = true
  }

  Process {
    id: arm
    property string ticket: ""
    property var pendingRequest: null
    stdout: StdioCollector { id: armOutput }
    onExited: {
      var completedTicket = ticket
      var completedRequest = pendingRequest
      pendingRequest = null
      root.completeArm(completedTicket, completedRequest, armOutput.text)
    }
  }
  Timer {
    interval: 55; repeat: true; running: root.active && root.phase !== "arming" && root.phase !== "handoff"
    onTriggered: if (!poll.running) {
      poll.ticket = root.token
      poll.command = root.command("return nocturneLaunch.status("+root.quote(root.token)+")")
      poll.running = true
    }
  }
  Process {
    id: poll
    stdout: StdioCollector { id: pollOutput }
    property string ticket: ""
    onExited: if (ticket === root.token) root.consumeStatus(pollOutput.text)
  }
  Process {
    id: handoff
    property string ticket: ""
    stdout: StdioCollector { id: handoffOutput }
    onExited: {
      if (!root.active || ticket !== root.token) return
      if (handoffOutput.text.trim() !== "ok") { root.cancel(); return }
      fadeOut.restart()
    }
  }
  NumberAnimation { id: fadeOut; target: root; property: "alpha"; to: 0; duration: 90; onFinished: root.finish() }
  Timer { id: timeout; interval: 7400; onTriggered: root.cancel() }
  Timer { id: settle; interval: 40; onTriggered: root.reveal() }
  Timer {
    id: animation; interval: 8; repeat: true
    onTriggered: {
      var now = Date.now(), dt = Math.min(0.032,(now-root.lastTick)/1000)
      root.lastTick = now; root.age += dt*1000
      while (dt > 0) {
        var step = Math.min(dt,1/240)
        root.velocity += (540*(1-root.progress)-34*root.velocity)*step
        root.progress += root.velocity*step; dt -= step
      }
      if ((root.age > 280 && Math.abs(root.progress-1)<0.0005 && Math.abs(root.velocity)<0.02) || root.age > 800) {
        stop(); settle.start()
      }
    }
  }
  Component.onDestruction: cancel()

  Variants {
    model: Quickshell.screens
    PanelWindow {
      id: window
      required property var modelData
      screen: modelData
      // Map origin and destination before motion crosses a screen boundary.
      visible: root.active && (root.intersects(root.origin, modelData)
        || root.intersects(root.destination, modelData) || root.intersects(root.geometry, modelData))
      anchors { left:true;right:true;top:true;bottom:true }
      exclusionMode: ExclusionMode.Ignore
      color: "transparent"
      WlrLayershell.namespace: "nocturne-launch-morph"
      WlrLayershell.layer: WlrLayer.Overlay
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
      mask: Region { width:0; height:0 }
      FrameAnimation {
        // Keep the source card until this surface has entered the render loop.
        // Two ticks let the first overlay buffer commit before hiding its source.
        running: root.active && window.backingWindowVisible && !root.readyOutputs[window.modelData.name]
        property int committedFrames: 0
        onRunningChanged: if (running) committedFrames = 0
        onTriggered: { committedFrames++; if (committedFrames >= 2) root.markOutputReady(window.modelData.name, false) }
      }
      Item {
        id: surface
        x: root.geometry.x - window.screen.x
        y: root.geometry.y - window.screen.y
        width: root.geometry.width; height: root.geometry.height
        Rectangle { anchors.fill: parent; color: root.surface }
        ScreencopyView {
          id: capture
          width: root.destination.width; height: root.destination.height
          anchors.centerIn: parent
          captureSource: window.visible ? root.target : null
          live: root.active && window.visible
          opacity: Math.max(0,Math.min(1,(root.progress-0.42)/0.48))
          onHasContentChanged: if (hasContent) root.markOutputReady(window.modelData.name, true)
          onStopped: Qt.callLater(function() {
            if (window.visible && root.phase === "moving" && !capture.hasContent) root.cancel()
          })
        }
        Item {
          width: root.origin.width; height: root.origin.height
          opacity: root.phase === "moving" || root.phase === "handoff" ? Math.max(0,1-root.age/110) : 1
          Rectangle {
            x: root.sourceVisual.iconX-3; y: root.sourceVisual.iconY-3
            width: root.sourceVisual.iconSize+6; height:width; radius:8
            color: Qt.rgba(root.foreground.r,root.foreground.g,root.foreground.b,0.16)
            border.color: Qt.rgba(root.foreground.r,root.foreground.g,root.foreground.b,0.20)
          }
          Image {
            x:root.sourceVisual.iconX; y:root.sourceVisual.iconY
            width:root.sourceVisual.iconSize; height:width
            source:root.icon; fillMode:Image.PreserveAspectFit
            sourceSize.width: width * Screen.devicePixelRatio
            sourceSize.height: height * Screen.devicePixelRatio
          }
          Text {
            x:root.sourceVisual.labelX; y:root.sourceVisual.labelY; width:root.sourceVisual.labelWidth
            text:root.label; textFormat:Text.PlainText; elide:Text.ElideRight
            font.family:root.fontFamily; font.pixelSize:root.fontSize; font.weight:Font.Medium; color:root.foreground
          }
          Text {
            x:root.sourceVisual.labelX; y:root.sourceVisual.detailY; width:root.sourceVisual.labelWidth
            text:root.sourceVisual.detail; textFormat:Text.PlainText; elide:Text.ElideRight
            font.family:root.fontFamily; font.pixelSize:root.sourceVisual.detailSize; color:root.foreground; opacity:0.68
          }
        }
      }
      ShaderEffectSource {
        id: surfaceTexture
        sourceItem: surface; hideSource: true; live: root.active
        sourceRect: Qt.rect(0,0,surface.width,surface.height)
        visible: false
      }
      ShaderEffect {
        readonly property real outset: root.nativeBorder * root.decorationMix
        x: surface.x-outset; y: surface.y-outset
        width: surface.width+outset*2; height: surface.height+outset*2
        opacity: root.alpha
        property var source: surfaceTexture
        property vector2d size: Qt.vector2d(width,height)
        property real extent: outset
        property real radius: root.startRadius+(root.endRadius-root.startRadius)*Math.min(1,root.progress)
        property real power: 2+(root.nativePower-2)*root.decorationMix
        property real thickness: 1+(root.nativeBorder-1)*root.decorationMix
        property real angle: root.nativeAngle
        property color firstColor: root.mixColor(root.edge,root.nativeFirst,root.decorationMix)
        property color lastColor: root.mixColor(root.edge,root.nativeLast,root.decorationMix)
        fragmentShader: Qt.resolvedUrl("morph-surface.frag.qsb")
      }
    }
  }
}
