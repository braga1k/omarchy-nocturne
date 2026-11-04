import QtQuick 2.15
import QtQuick.Window 2.15
Window {
  visible: true; width: 960; height: 640; title: "Nocturne demo — Music"; color: "#181a28"
  Rectangle { width: 192; height: parent.height; color: "#141622"
    Column { x: 28; y: 32; spacing: 26
      Text { text:"Music";font.family:"Noto Sans";font.pixelSize:24;font.bold:true;color:"#e8e4ff" }
      Repeater {model:["Listen now","Library","Playlists","Recently added"]
        Text {required property string modelData;text:modelData;font.family:"Noto Sans";font.pixelSize:14;color:modelData==="Listen now"?"#aba7eb":"#989db5"} }
    }
  }
  Column { x: 228; y: 40; spacing: 22; width:parent.width-264
    Text { text:"Made for this moment";font.family:"Noto Sans";font.pixelSize:26;font.bold:true;color:"#e8e4ff" }
    Text { text:"A quiet space for your favourite sounds.";font.family:"Noto Sans";font.pixelSize:14;color:"#a5abc3" }
    Row { spacing: 20
      Repeater {model:["Late hours","Soft focus","First light"]
        Column {required property string modelData;spacing:12
          Rectangle {width:152;height:152;radius:12;gradient:Gradient {GradientStop {position:0;color:modelData==="Late hours"?"#9d92d2":modelData==="Soft focus"?"#668f9e":"#b6a18c"} GradientStop {position:1;color:"#30334f"}}
            Rectangle {anchors.centerIn:parent;width:70;height:70;radius:35;color:"transparent";border.width:1;border.color:"#66ffffff"}
          }
          Text {text:modelData;font.family:"Noto Sans";font.pixelSize:14;color:"#e8e4ff"}
        }
      }
    }
  }
}
