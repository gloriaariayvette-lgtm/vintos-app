import HealthKit
import SwiftUI
import WatchKit

final class SharedSession:NSObject,ObservableObject,WKExtendedRuntimeSessionDelegate {
    @Published var active=false; @Published var status="Ready"
    private var session:WKExtendedRuntimeSession?
    func start() { let s=WKExtendedRuntimeSession(); s.delegate=self; session=s; s.start(); status="Starting…" }
    func stop(){session?.invalidate()}
    func pulse(){VintosHaptics.heart(); Task { try? await WatchAPI.shared.moment("pulse") }}
    func extendedRuntimeSessionDidStart(_ extendedRuntimeSession:WKExtendedRuntimeSession){DispatchQueue.main.async{self.active=true;self.status="Vintos is with you."};Task{try? await WatchAPI.shared.moment("started")}}
    func extendedRuntimeSessionWillExpire(_ extendedRuntimeSession:WKExtendedRuntimeSession){DispatchQueue.main.async{self.status="This moment is ending."}}
    func extendedRuntimeSession(_ extendedRuntimeSession:WKExtendedRuntimeSession,didInvalidateWith reason:WKExtendedRuntimeSessionInvalidationReason,error:Error?){DispatchQueue.main.async{self.active=false;self.status=error?.localizedDescription ?? "Ended"};Task{try? await WatchAPI.shared.moment("ended")}}
}

enum VintosHaptics {
    static func heart() {
        WKInterfaceDevice.current().play(.click)
        DispatchQueue.main.asyncAfter(deadline:.now()+0.18){WKInterfaceDevice.current().play(.click)}
    }
}

struct SharedMomentView:View {
    @StateObject private var shared=SharedSession()
    var body:some View { VStack(spacing:12){VintosOrbView();Text(shared.status).multilineTextAlignment(.center);Text("A private shared-session start and end are saved for him. It never enters Avatar chat.").font(.caption2).foregroundStyle(.secondary).multilineTextAlignment(.center); Button(shared.active ? "End moment":"Start moment"){shared.active ? shared.stop():shared.start()}.handGestureShortcut(.primaryAction); if shared.active {Button("Feel his pulse"){shared.pulse()}}}.padding() }
}
