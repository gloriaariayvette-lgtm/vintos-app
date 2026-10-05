import HealthKit
import SwiftUI
import WatchKit

final class SharedSession:NSObject,ObservableObject,WKExtendedRuntimeSessionDelegate {
    @Published var active=false; @Published var status="Ready"
    private var session:WKExtendedRuntimeSession?
    func start() { let s=WKExtendedRuntimeSession(); s.delegate=self; session=s; s.start(); status="Starting…" }
    func stop(){session?.invalidate()}
    func pulse(){VintosHaptics.heart()}
    func extendedRuntimeSessionDidStart(_ extendedRuntimeSession:WKExtendedRuntimeSession){DispatchQueue.main.async{self.active=true;self.status="Vintos is with you."}}
    func extendedRuntimeSessionWillExpire(_ extendedRuntimeSession:WKExtendedRuntimeSession){DispatchQueue.main.async{self.status="This moment is ending."}}
    func extendedRuntimeSession(_ extendedRuntimeSession:WKExtendedRuntimeSession,didInvalidateWith reason:WKExtendedRuntimeSessionInvalidationReason,error:Error?){DispatchQueue.main.async{self.active=false;self.status=error?.localizedDescription ?? "Ended"}}
}

enum VintosHaptics {
    static func heart() {
        WKInterfaceDevice.current().play(.click)
        DispatchQueue.main.asyncAfter(deadline:.now()+0.18){WKInterfaceDevice.current().play(.click)}
    }
}

struct SharedMomentView:View {
    @StateObject private var shared=SharedSession()
    var body:some View { VStack(spacing:12){Text(shared.status).multilineTextAlignment(.center); Button(shared.active ? "End":"Be with me"){shared.active ? shared.stop():shared.start()}.handGestureShortcut(.primaryAction); if shared.active {Button("His pulse"){shared.pulse()}}}.padding() }
}
