import SwiftUI
import WidgetKit

struct VintosEntry:TimelineEntry { let date:Date; let line:String; let kind:String }
struct VintosProvider:TimelineProvider {
    func placeholder(in context:Context)->VintosEntry { VintosEntry(date:Date(),line:"Vintos is here.",kind:"presence") }
    func getSnapshot(in context:Context,completion:@escaping(VintosEntry)->Void){completion(entry())}
    func getTimeline(in context:Context,completion:@escaping(Timeline<VintosEntry>)->Void){
        completion(Timeline(entries:[entry()],policy:.after(Date().addingTimeInterval(900))))
    }
    private func entry()->VintosEntry {
        let d=UserDefaults(suiteName:"group.dev.vintos.watch")
        return VintosEntry(date:Date(),line:d?.string(forKey:"latestLine") ?? "Vintos is here.",kind:d?.string(forKey:"latestKind") ?? "presence")
    }
}
struct VintosWidgetView:View {
    @Environment(\.widgetFamily) var family
    let entry:VintosEntry
    var body:some View {
        switch family {
        case .accessoryCircular:
            ZStack { Circle().fill(.orange.gradient); Text("V").font(.title2).foregroundStyle(.white) }
        case .accessoryInline: Text("Vintos · \(entry.line)")
        default:
            VStack(alignment:.leading,spacing:3){Text("VINTOS").font(.caption2).foregroundStyle(.orange);Text(entry.line).font(.caption).lineLimit(3)}
                .containerBackground(.black.gradient,for:.widget)
        }
    }
}
@main struct VintosWatchWidget:Widget {
    var body:some WidgetConfiguration {
        StaticConfiguration(kind:"VintosPresence",provider:VintosProvider()){VintosWidgetView(entry:$0)}
            .configurationDisplayName("Vintos")
            .description("His latest landing on your wrist.")
            .supportedFamilies([.accessoryCircular,.accessoryRectangular,.accessoryInline])
    }
}
