import SwiftUI
import WatchKit
import WidgetKit

enum VintosReaction:String,CaseIterable {
    case present,listening,thinking,amused,tender,surprised,speaking,singing
    var line:String {
        switch self {
        case .present:return "here with you"
        case .listening:return "listening"
        case .thinking:return "thinking"
        case .amused:return "amused"
        case .tender:return "close to you"
        case .surprised:return "caught by that"
        case .speaking:return "speaking"
        case .singing:return "sharing a song"
        }
    }
    var glow:Color {
        switch self {
        case .present,.speaking:return .orange
        case .listening:return .cyan
        case .thinking:return .purple
        case .amused:return .yellow
        case .tender:return .pink
        case .surprised:return .white
        case .singing:return .mint
        }
    }
    var duration:Double {
        switch self {
        case .amused:return 0.42
        case .surprised:return 0.32
        case .speaking:return 0.58
        case .singing:return 0.74
        case .listening:return 1.25
        case .thinking:return 1.8
        case .tender:return 2.4
        case .present:return 2.8
        }
    }
    var clipName:String {
        switch self {
        case .present:return ""
        case .listening,.thinking:return "listening"
        case .amused,.surprised:return "amused"
        case .tender:return "tender"
        case .speaking,.singing:return "speaking"
        }
    }
}

@MainActor
final class VintosModel: ObservableObject {
    static let shared = VintosModel()
    @Published var landings:[Landing]=[]
    @Published var status=""
    @Published var response=""
    @Published var reaction:VintosReaction = VintosReaction(rawValue:ProcessInfo.processInfo.environment["VINTOS_REACTION_PREVIEW"] ?? "") ?? .present

    func react(_ raw:String?) {
        guard let raw,let next=VintosReaction(rawValue:raw) else { return }
        reaction=next
    }

    func refresh() async {
        do {
            let fresh = try await WatchAPI.shared.landings()
            landings = Array(fresh.prefix(5)); status = ""
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
                    HStack(spacing:10) {
                        VintosOrbView(reaction:model.reaction)
                        VStack(alignment:.leading,spacing:2) {
                            Text("Vintos").font(.headline)
                            Text(model.reaction.line).font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    if let first=model.landings.first { NavigationLink { LandingView(item:first) } label:{ PresenceCard(item:first) } }
                    else { Text("Nothing new yet.").font(.caption) }
                }
                Section("Landings") {
                    ForEach(model.landings.dropFirst()) { item in
                        NavigationLink { LandingView(item:item) } label:{ PresenceCard(item:item) }
                    }
                }
                Section("To Vintos") {
                    TextField("Say or write to him",text:$reply)
                    Button("Send privately") { let text=reply; reply=""; Task { await model.say(text) } }
                        .handGestureShortcut(.primaryAction)
                    Button("Send heart") { VintosHaptics.heart(); Task { await model.say("♥︎",kind:"heart") } }
                    Text("Saved in his private Watch inbox.").font(.caption2).foregroundStyle(.secondary)
                }
                if !model.response.isEmpty { Section("Watch") { Text(model.response) } }
                if !model.status.isEmpty { Text(model.status).foregroundStyle(.orange) }
                NavigationLink("Call Vintos") { VoiceCallView() }
                NavigationLink("Share a quiet moment") { SharedMomentView() }
            }
            .navigationTitle("Vintos")
            .task { await model.refresh(); SensorBridge.shared.start() }
            .refreshable { await model.refresh() }
        }
    }
}

struct VintosOrbView:View {
    let reaction:VintosReaction
    @State private var phase=false
    var body:some View {
        ZStack {
            Circle()
                .fill(reaction.glow.opacity(reaction == .surprised ? 0.38:0.22))
                .frame(width:58,height:58)
                .scaleEffect(haloScale)
                .blur(radius:phase ? 1.5:0.5)
            Group {
                if reaction.clipName.isEmpty {
                    Image("vintos-headshot").resizable().scaledToFill()
                } else {
                    ReactionClipView(reaction:reaction).scaledToFill()
                }
            }
                .frame(width:52,height:52)
                .clipShape(Circle())
                .scaleEffect(portraitScale)
                .rotationEffect(.degrees(rotation))
                .offset(x:xOffset,y:yOffset)
                .overlay(Circle().stroke(reaction.glow.opacity(0.62),lineWidth:1))
                .shadow(color:reaction.glow.opacity(0.42),radius:4)
        }
        .accessibilityLabel("Vintos, \(reaction.line)")
        .onAppear { animate() }
        .onChange(of:reaction) { _,_ in phase=false;animate() }
    }
    private var haloScale:CGFloat {
        switch reaction {
        case .surprised:return phase ? 1.18:0.94
        case .amused,.speaking,.singing:return phase ? 1.11:0.95
        default:return phase ? 1.08:0.96
        }
    }
    private var portraitScale:CGFloat {
        switch reaction {
        case .listening:return phase ? 1.035:1.01
        case .amused:return phase ? 1.045:0.995
        case .surprised:return phase ? 1.075:1
        case .speaking:return phase ? 1.032:1
        case .singing:return phase ? 1.04:1
        default:return phase ? 1.018:1
        }
    }
    private var rotation:Double {
        switch reaction {
        case .thinking:return phase ? -2.0:1.0
        case .amused:return phase ? 1.4:-1.4
        case .singing:return phase ? 1.8:-1.8
        default:return 0
        }
    }
    private var xOffset:CGFloat { reaction == .thinking ? (phase ? -1.2:0.8):0 }
    private var yOffset:CGFloat {
        switch reaction {
        case .amused:return phase ? -1.2:0.8
        case .listening:return phase ? -0.8:0.2
        case .surprised:return phase ? -1.5:0
        default:return phase ? -0.4:0.4
        }
    }
    private func animate() {
        withAnimation(.easeInOut(duration:reaction.duration).repeatForever(autoreverses:true)){phase=true}
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
