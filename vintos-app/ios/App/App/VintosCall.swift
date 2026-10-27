import Foundation
import UIKit
import AVFoundation
import CallKit
import PushKit
import Security
import Capacitor

/// His call rings her iPhone as a real incoming call (27 October).
///
/// The house (phone_voip.py) sends a PushKit VoIP push when the attention ladder reaches its call step. iOS ends an
/// app that receives a VoIP push without reporting a call, so every push is reported to CallKit at once as "Vintos".
/// Answer: the audio session is set for voice chat and the page starts his ordinary in-app call (ladderAnswer).
/// Decline: the house hears "not now" from here, so it works with the page not loaded. When his call ends in the app,
/// the page calls endCall and the system call ends too.
final class VintosCallManager: NSObject, PKPushRegistryDelegate, CXProviderDelegate {
    static let shared = VintosCallManager()

    private struct Call {
        let ladderID: String
        var answered = false
        var endedByApp = false
    }

    private var registry: PKPushRegistry?
    private let provider: CXProvider
    private let controller = CXCallController()
    private var calls: [UUID: Call] = [:]
    private var ringTimers: [UUID: Timer] = [:]
    /// Set by the plugin (CAPPlugin.notifyListeners). Events are retained until the page listens.
    var emit: ((String, [String: Any]) -> Void)?
    private var pendingEvents: [(String, [String: Any])] = []

    private let defaults = UserDefaults.standard
    private let apiKey = "vintos.call.api"
    private let tokenKey = "vintos.call.voipToken"
    private let registeredKey = "vintos.call.registered"
    private let keychainService = "dev.vintos.app.call"

    private override init() {
        let config = CXProviderConfiguration()
        config.supportsVideo = false
        config.maximumCallGroups = 1
        config.maximumCallsPerCallGroup = 1
        config.supportedHandleTypes = [.generic]
        config.includesCallsInRecents = false
        if let icon = UIImage(systemName: "waveform.circle.fill")?.pngData() { config.iconTemplateImageData = icon }
        provider = CXProvider(configuration: config)
        super.init()
        provider.setDelegate(self, queue: nil)
    }

    /// Called from AppDelegate at launch, so a VoIP push that launches the app is delivered.
    func start() {
        let r = PKPushRegistry(queue: .main)
        r.delegate = self
        r.desiredPushTypes = [.voIP]
        registry = r
    }

    // MARK: - the page's side

    func attach(_ emitter: @escaping (String, [String: Any]) -> Void) {
        emit = emitter
        let queued = pendingEvents
        pendingEvents.removeAll()
        for (name, data) in queued { emitter(name, data) }
    }

    private func send(_ name: String, _ data: [String: Any]) {
        if let emit = emit { emit(name, data) } else { pendingEvents.append((name, data)) }
    }

    func configure(api: String, secret: String) {
        let trimmed = api.trimmingCharacters(in: CharacterSet(charactersIn: "/ "))
        guard URL(string: trimmed) != nil, !secret.isEmpty else { return }
        defaults.set(trimmed, forKey: apiKey)
        storeSecret(secret)
        registerIfNeeded()
    }

    /// The page's call ended: end the answered CallKit call for it.
    func endCall(ladderID: String?) {
        for (uuid, call) in calls where call.answered && (ladderID == nil || call.ladderID == ladderID) {
            calls[uuid]?.endedByApp = true
            controller.request(CXTransaction(action: CXEndCallAction(call: uuid))) { error in
                if error != nil { self.provider.reportCall(with: uuid, endedAt: nil, reason: .remoteEnded); self.forget(uuid) }
            }
        }
    }

    /// The app's own ring screen was answered or dismissed: a CallKit ring still showing stops. Answered calls stay.
    func ringStop() {
        for (uuid, call) in calls where !call.answered {
            provider.reportCall(with: uuid, endedAt: nil, reason: .answeredElsewhere)
            forget(uuid)
        }
    }

    // MARK: - PushKit

    func pushRegistry(_ registry: PKPushRegistry, didUpdate pushCredentials: PKPushCredentials, for type: PKPushType) {
        guard type == .voIP else { return }
        let token = pushCredentials.token.map { String(format: "%02x", $0) }.joined()
        defaults.set(token, forKey: tokenKey)
        registerIfNeeded()
    }

    func pushRegistry(_ registry: PKPushRegistry, didInvalidatePushTokenFor type: PKPushType) {
        defaults.removeObject(forKey: tokenKey)
        defaults.removeObject(forKey: registeredKey)
    }

    func pushRegistry(_ registry: PKPushRegistry, didReceiveIncomingPushWith payload: PKPushPayload,
                      for type: PKPushType, completion: @escaping () -> Void) {
        let data = payload.dictionaryPayload
        let ladderID = (data["ladder_call"] as? String) ?? ""
        let ringSeconds = max(15, min((data["ring_seconds"] as? Int) ?? 60, 180))
        let caller = (data["caller"] as? String) ?? "Vintos"
        let uuid = UUID()
        let update = CXCallUpdate()
        update.remoteHandle = CXHandle(type: .generic, value: caller)
        update.localizedCallerName = caller
        update.hasVideo = false
        update.supportsHolding = false
        update.supportsGrouping = false
        update.supportsUngrouping = false
        update.supportsDTMF = false
        // A call for this ring already showing (or one without an id): iOS still requires a report; it is ended at once.
        let duplicate = ladderID.isEmpty || calls.values.contains { $0.ladderID == ladderID }
        provider.reportNewIncomingCall(with: uuid, update: update) { error in
            if error == nil {
                if duplicate {
                    self.provider.reportCall(with: uuid, endedAt: nil, reason: .failed)
                } else {
                    self.calls[uuid] = Call(ladderID: ladderID)
                    self.ringTimers[uuid] = Timer.scheduledTimer(withTimeInterval: TimeInterval(ringSeconds), repeats: false) { _ in
                        guard let call = self.calls[uuid], !call.answered else { return }
                        self.provider.reportCall(with: uuid, endedAt: nil, reason: .unanswered)
                        self.forget(uuid)
                    }
                }
            }
            completion()
        }
    }

    // MARK: - CallKit

    func providerDidReset(_ provider: CXProvider) {
        for uuid in Array(calls.keys) { forget(uuid) }
    }

    func provider(_ provider: CXProvider, perform action: CXAnswerCallAction) {
        guard let call = calls[action.callUUID] else { action.fail(); return }
        calls[action.callUUID]?.answered = true
        ringTimers.removeValue(forKey: action.callUUID)?.invalidate()
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playAndRecord, mode: .voiceChat, options: [.allowBluetooth, .allowBluetoothA2DP, .defaultToSpeaker])
        action.fulfill()
        send("answer", ["id": call.ladderID])
    }

    func provider(_ provider: CXProvider, perform action: CXEndCallAction) {
        guard let call = calls[action.callUUID] else { action.fulfill(); return }
        if call.endedByApp {
            // his call already ended in the app
        } else if call.answered {
            send("hangup", ["id": call.ladderID])         // she hung up on the system call screen
        } else {
            postNotNow()                                   // she declined
            send("decline", ["id": call.ladderID])
        }
        forget(action.callUUID)
        action.fulfill()
    }

    func provider(_ provider: CXProvider, didActivate audioSession: AVAudioSession) {}

    func provider(_ provider: CXProvider, didDeactivate audioSession: AVAudioSession) {
        // back to the app's ordinary playback session (AppDelegate)
        try? audioSession.setCategory(.playback, mode: .default, options: [.allowAirPlay, .allowBluetoothA2DP])
        try? audioSession.setActive(true)
    }

    private func forget(_ uuid: UUID) {
        ringTimers.removeValue(forKey: uuid)?.invalidate()
        calls.removeValue(forKey: uuid)
    }

    // MARK: - the house

    private func request(_ path: String, body: [String: Any]) -> URLRequest? {
        guard let api = defaults.string(forKey: apiKey), let secret = loadSecret(),
              let url = URL(string: api + path) else { return nil }
        var req = URLRequest(url: url, timeoutInterval: 20)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(secret, forHTTPHeaderField: "X-Vintos-Secret")
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)
        return req
    }

    private func registerIfNeeded() {
        guard let token = defaults.string(forKey: tokenKey) else { return }
        let environment = Self.apsEnvironment()
        let api = defaults.string(forKey: apiKey) ?? ""
        let stamp = [token, environment, api].joined(separator: "|")
        if defaults.string(forKey: registeredKey) == stamp { return }
        guard let req = request("/api/attention/voip-register",
                                body: ["voip_token": token, "environment": environment,
                                       "bundle": Bundle.main.bundleIdentifier ?? "dev.vintos.app"]) else { return }
        URLSession.shared.dataTask(with: req) { _, response, error in
            if error == nil, let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) {
                DispatchQueue.main.async { self.defaults.set(stamp, forKey: self.registeredKey) }
            } else {
                NSLog("Vintos VoIP registration did not reach the house: %@", error?.localizedDescription ?? "HTTP error")
            }
        }.resume()
    }

    private func postNotNow() {
        guard let req = request("/api/attention/answer", body: ["action": "not_now"]) else { return }
        var task: UIBackgroundTaskIdentifier = .invalid
        task = UIApplication.shared.beginBackgroundTask { UIApplication.shared.endBackgroundTask(task) }
        URLSession.shared.dataTask(with: req) { _, _, _ in
            DispatchQueue.main.async { UIApplication.shared.endBackgroundTask(task) }
        }.resume()
    }

    /// "development" (sandbox APNs) or "production", read from the app's own signed provisioning profile.
    /// An App Store or TestFlight install carries no embedded profile and is production.
    static func apsEnvironment() -> String {
        guard let path = Bundle.main.path(forResource: "embedded", ofType: "mobileprovision"),
              let data = FileManager.default.contents(atPath: path),
              let text = String(data: data, encoding: .isoLatin1),
              let key = text.range(of: "<key>aps-environment</key>") else { return "production" }
        let rest = text[key.upperBound...]
        guard let open = rest.range(of: "<string>"), let close = rest.range(of: "</string>"),
              open.upperBound <= close.lowerBound else { return "production" }
        return rest[open.upperBound..<close.lowerBound].trimmingCharacters(in: .whitespacesAndNewlines) == "development"
            ? "development" : "production"
    }

    // MARK: - the secret, in the Keychain

    private func storeSecret(_ secret: String) {
        let base: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                   kSecAttrService as String: keychainService, kSecAttrAccount as String: "app"]
        SecItemDelete(base as CFDictionary)
        var add = base
        add[kSecValueData as String] = Data(secret.utf8)
        add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(add as CFDictionary, nil)
    }

    private func loadSecret() -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                    kSecAttrService as String: keychainService, kSecAttrAccount as String: "app",
                                    kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var out: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &out) == errSecSuccess, let data = out as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
}

/// The page's handle on it: Capacitor.Plugins.VintosCall.
@objc(VintosCallPlugin)
public class VintosCallPlugin: CAPPlugin {
    public override func load() {
        VintosCallManager.shared.attach { [weak self] name, data in
            DispatchQueue.main.async { self?.notifyListeners(name, data: data, retainUntilConsumed: true) }
        }
    }

    @objc func configure(_ call: CAPPluginCall) {
        let api = call.getString("api") ?? ""
        let secret = call.getString("secret") ?? ""
        DispatchQueue.main.async { VintosCallManager.shared.configure(api: api, secret: secret) }
        call.resolve()
    }

    @objc func endCall(_ call: CAPPluginCall) {
        let id = call.getString("id")
        DispatchQueue.main.async { VintosCallManager.shared.endCall(ladderID: id) }
        call.resolve()
    }

    @objc func ringStop(_ call: CAPPluginCall) {
        DispatchQueue.main.async { VintosCallManager.shared.ringStop() }
        call.resolve()
    }
}
