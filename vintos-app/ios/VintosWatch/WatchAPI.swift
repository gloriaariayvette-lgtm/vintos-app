import Foundation

struct Track: Codable, Hashable { let src: String?; let version: Int? }
struct LandingPiece: Codable, Hashable {
    let type: String?; let title: String?; let text: String?; let src: String?; let tracks: [Track]?
}
struct Landing: Codable, Identifiable, Hashable {
    var id: String { surface + ":" + ref }
    let surface: String; let ref: String; let at: String; let piece: LandingPiece; let noted: Bool?
}
struct LandingEnvelope: Codable { let items: [Landing] }
struct WatchReply: Codable { let reply: String? }
struct VoiceFramingEnvelope:Codable { let framing:String? }

actor WatchAPI {
    static let shared = WatchAPI()
    private let session: URLSession = .shared
    nonisolated let baseURL: URL
    private let bearer: String

    init(bundle: Bundle = .main) {
        let raw = bundle.object(forInfoDictionaryKey: "VintosWatchBaseURL") as? String ?? ""
        baseURL = URL(string: raw) ?? URL(string: "https://invalid.invalid")!
        bearer = bundle.object(forInfoDictionaryKey: "VintosWatchToken") as? String ?? ""
    }

    private func request(_ path: String, method: String = "GET", json: Any? = nil) throws -> URLRequest {
        guard !bearer.isEmpty else { throw URLError(.userAuthenticationRequired) }
        var req = URLRequest(url: baseURL.appendingPathComponent(path))
        req.httpMethod = method
        req.setValue("Bearer \(bearer)", forHTTPHeaderField: "Authorization")
        if let json { req.httpBody = try JSONSerialization.data(withJSONObject: json); req.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        req.timeoutInterval = 30
        return req
    }

    private func data(_ req: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: req)
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else { throw URLError(.badServerResponse) }
        return data
    }

    func landings() async throws -> [Landing] {
        let data = try await data(request("api/watch/landings"))
        return try JSONDecoder().decode(LandingEnvelope.self, from: data).items
    }

    func register(deviceToken: String) async throws {
        _ = try await data(request("api/watch/register", method:"POST", json:["device_token":deviceToken,"environment":"development"]))
    }

    func reply(kind: String, text: String, messageID: String = "") async throws -> String {
        let payload:[String:Any] = ["kind":kind,"text":text,"message_id":messageID,
                                    "observed_at":ISO8601DateFormatter().string(from:Date())]
        let received = try await data(request("api/watch/reply",method:"POST",json:payload))
        let value = try JSONDecoder().decode(WatchReply.self, from: received)
        return value.reply ?? ""
    }

    func land(surface:String, ref:String, rating:String, why:String, before:String="") async throws {
        _ = try await data(request("api/watch/landing",method:"POST",json:["surface":surface,"ref":ref,"rating":rating,"why":why,"before":before]))
    }

    func telemetry(_ samples:[[String:Any]], asleep:Bool) async throws {
        _ = try await data(request("api/watch/telemetry",method:"POST",json:["samples":samples,"asleep":asleep]))
    }

    func moment(_ state:String) async throws {
        _ = try await data(request("api/watch/moment",method:"POST",json:[
            "state":state,"observed_at":ISO8601DateFormatter().string(from:Date())]))
    }

    func voiceToken(provider:String) async throws -> VoiceTokenEnvelope {
        var components=URLComponents(url:baseURL.appendingPathComponent("api/voice/token"),resolvingAgainstBaseURL:false)!
        components.queryItems=[URLQueryItem(name:"provider",value:provider)]
        var req=URLRequest(url:components.url!);req.httpMethod="POST";req.setValue("Bearer \(bearer)",forHTTPHeaderField:"Authorization")
        return try JSONDecoder().decode(VoiceTokenEnvelope.self,from:await data(req))
    }

    func voiceFraming() async throws -> String {
        let received=try await data(request("api/voice/framing"))
        return try JSONDecoder().decode(VoiceFramingEnvelope.self,from:received).framing ?? ""
    }

    func localTurn(audio:String,instructions:String,framing:String) async throws -> LocalVoiceEnvelope {
        let received=try await data(request("api/watch/voice/local/turn",method:"POST",json:[
            "audio":audio,"sample_rate":24000,"instructions":instructions,"framing":framing]))
        return try JSONDecoder().decode(LocalVoiceEnvelope.self,from:received)
    }

    func localHeartbeat() async throws { _ = try await data(request("api/watch/voice/local/heartbeat",method:"POST",json:[:])) }
    func localEnd() async throws { _ = try await data(request("api/watch/voice/local/end",method:"POST",json:[:])) }

    func voiceLedger(gloria:String,vintos:String,provider:String,clientID:String) async throws {
        _ = try await data(request("api/voice/ledger",method:"POST",json:[
            "gloria":gloria,"vintos":vintos,"provider":provider,"client_session_id":clientID,
            "turn_id":"\(clientID):\(UUID().uuidString)","playback_state":"completed","interrupted":false]))
    }

    func voiceEnd(provider:String,clientID:String,duration:Int) async throws {
        _ = try await data(request("api/voice/session-end",method:"POST",json:[
            "provider":provider,"client_session_id":clientID,"duration_seconds":duration]))
    }

    nonisolated func absolute(_ path:String?) -> URL? {
        guard let path, !path.isEmpty else { return nil }
        if let url=URL(string:path), url.scheme != nil { return url }
        return URL(string:path,relativeTo:baseURL)?.absoluteURL
    }
}
