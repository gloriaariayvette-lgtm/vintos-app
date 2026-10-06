import SwiftUI
import UserNotifications
import WatchKit

@main
struct VintosWatchApp: App {
    @WKApplicationDelegateAdaptor(WatchAppDelegate.self) var delegate
    @StateObject private var model = VintosModel.shared

    var body: some Scene {
        WindowGroup { ContentView().environmentObject(model) }
    }
}

final class WatchAppDelegate: NSObject, WKApplicationDelegate, UNUserNotificationCenterDelegate {
    private func applyReaction(_ info:[String:Any]) {
        DispatchQueue.main.async { VintosModel.shared.react(info["reaction"] as? String) }
    }
    func applicationDidFinishLaunching() {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        let play = UNNotificationAction(identifier: "PLAY", title: "Play", options: [.foreground])
        let reply = UNTextInputNotificationAction(identifier: "REPLY", title: "Reply", options: [.foreground],
                                                   textInputButtonTitle: "Send", textInputPlaceholder: "say it to him…")
        let heart = UNNotificationAction(identifier: "HEART", title: "Send heart", options: [.foreground])
        center.setNotificationCategories([
            UNNotificationCategory(identifier: "VINTOS_SONG", actions: [play, reply, heart], intentIdentifiers: ["INSendMessageIntent"]),
            UNNotificationCategory(identifier: "VINTOS_PAINTING", actions: [reply, heart], intentIdentifiers: ["INSendMessageIntent"]),
            UNNotificationCategory(identifier: "VINTOS_MESSAGE", actions: [reply, heart], intentIdentifiers: ["INSendMessageIntent"])
        ])
        #if !targetEnvironment(simulator)
        center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
            if granted { DispatchQueue.main.async { WKExtension.shared().registerForRemoteNotifications() } }
        }
        #endif
        SensorBridge.shared.start()
    }

    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        Task { try? await WatchAPI.shared.register(deviceToken: token) }
    }

    func didFailToRegisterForRemoteNotificationsWithError(_ error: Error) {
        VintosModel.shared.status = "Notifications could not register: \(error.localizedDescription)"
    }

    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse,
                                withCompletionHandler completionHandler: @escaping () -> Void) {
        let info = response.notification.request.content.userInfo["vintos"] as? [String: Any] ?? [:]
        applyReaction(info)
        let messageID = info["message_id"] as? String ?? ""
        switch response.actionIdentifier {
        case "PLAY":
            if let raw = info["media_url"] as? String, let url = WatchAPI.shared.absolute(raw) { AudioPlayer.shared.play(url) }
        case "REPLY":
            let text = (response as? UNTextInputNotificationResponse)?.userText ?? ""
            Task { _ = try? await WatchAPI.shared.reply(kind: "dictation", text: text, messageID: messageID) }
        case "HEART":
            VintosHaptics.heart()
            Task { _ = try? await WatchAPI.shared.reply(kind: "heart", text: "♥︎", messageID: messageID) }
        default: break
        }
        completionHandler()
    }

    func userNotificationCenter(_ center:UNUserNotificationCenter,willPresent notification:UNNotification,
                                withCompletionHandler completionHandler:@escaping(UNNotificationPresentationOptions)->Void) {
        let info=notification.request.content.userInfo["vintos"] as? [String:Any] ?? [:]
        applyReaction(info)
        completionHandler([.banner,.sound])
    }
}
