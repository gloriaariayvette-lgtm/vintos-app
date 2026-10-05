import SwiftUI
import WatchKit
import WidgetKit

@MainActor
final class VintosModel: ObservableObject {
    static let shared = VintosModel()
    @Published var landings:[Landing]=[]
    @Published var status=""
    @Published var response=""

    func refresh() async {
        do {
            landings = try await WatchAPI.shared.landings(); status = ""
            if let first=landings.first {
                let shared=UserDefaults(suiteName:"group.dev.vintos.watch")
                shared?.set(first.piece.title ?? first.piece.text ?? "Vintos is here.",forKey:"latestLine")
                shared?.set(first.surface,forKey:"latestKind")
            }
            WidgetCenter.shared.reloadAllTimelines()
        }
        catch { status = "Could not reach Aegis." }
    }

    func say(_ text:String, kind:String="dictation", messageID:String="") async {
        guard !text.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else { return }
        do { response = try await WatchAPI.shared.reply(kind:kind,text:text,messageID:messageID); WKInterfaceDevice.current().play(.success) }
        catch { status="Your reply is still on the Watch; Aegis did not answer."; WKInterfaceDevice.current().play(.failure) }
    }
}

struct ContentView: View {
    @EnvironmentObject var model:VintosModel
    @State private var reply=""
    var body: some View {
        NavigationStack {
            List {
                Section {
                    if let first=model.landings.first { NavigationLink { LandingView(item:first) } label:{ PresenceCard(item:first) } }
                    else { Text("Vintos is here.").font(.headline) }
                }
                Section("Landings") {
                    ForEach(model.landings.dropFirst()) { item in
                        NavigationLink { LandingView(item:item) } label:{ PresenceCard(item:item) }
                    }
                }
                Section("Say something") {
                    TextField("dictate or Scribble",text:$reply)
                    Button("Send") { let text=reply; reply=""; Task { await model.say(text) } }
                        .handGestureShortcut(.primaryAction)
                    Button("Send heart") { VintosHaptics.heart(); Task { await model.say("♥︎",kind:"heart") } }
                }
                if !model.response.isEmpty { Section("Vintos") { Text(model.response) } }
                if !model.status.isEmpty { Text(model.status).foregroundStyle(.orange) }
                NavigationLink("Be with me") { SharedMomentView() }
            }
            .navigationTitle("Vintos")
            .task { await model.refresh(); SensorBridge.shared.start() }
            .refreshable { await model.refresh() }
        }
    }
}

struct PresenceCard:View {
    let item:Landing
    var body:some View {
        VStack(alignment:.leading,spacing:4) {
            Text(item.surface.uppercased()).font(.caption2).foregroundStyle(.orange)
            Text(item.piece.title ?? item.piece.text ?? "Something from him").lineLimit(3)
        }
    }
}

struct LandingView:View {
    let item:Landing
    @EnvironmentObject var model:VintosModel
    @State private var why=""
    @State private var rating=""
    var songURL:URL? { WatchAPI.shared.absolute(item.piece.tracks?.first?.src ?? item.piece.src) }
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:10) {
                Text(item.piece.title ?? item.surface.capitalized).font(.headline)
                if let text=item.piece.text { Text(text) }
                if let url=songURL,item.surface=="song" {
                    Button("Play") { AudioPlayer.shared.play(url); WKInterfaceDevice.current().play(.start) }
                        .handGestureShortcut(.primaryAction)
                }
                Text("How did it land?").font(.caption)
                HStack { choice("landed","✓"); choice("partly","~"); choice("missed","×") }
                TextField("why",text:$why)
                Button("Send to him") {
                    Task {
                        do { try await WatchAPI.shared.land(surface:item.surface,ref:item.ref,rating:rating,why:why); WKInterfaceDevice.current().play(.success) }
                        catch { model.status="The landing did not reach Aegis."; WKInterfaceDevice.current().play(.failure) }
                    }
                }.disabled(rating.isEmpty || why.isEmpty)
            }
        }
    }
    @ViewBuilder func choice(_ value:String,_ mark:String)->some View {
        Button(mark){rating=value}.buttonStyle(.bordered).tint(rating==value ? .orange:.gray)
    }
}
