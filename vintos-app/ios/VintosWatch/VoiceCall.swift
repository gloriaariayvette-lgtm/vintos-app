import AVFoundation
import Foundation
import SwiftUI
import WatchKit

enum WatchVoiceProvider:String,CaseIterable,Identifiable {
    case grok,openai,local
    var id:String { rawValue }
    var title:String {
        switch self {
        case .grok:return "Grok live"
        case .openai:return "ChatGPT live"
        case .local:return "Vintos Local"
        }
    }
}

struct VoiceTokenEnvelope:Decodable {
    let token:String
    let instructions:String
    let provider:String?
    let error:String?
}

struct LocalVoiceEnvelope:Decodable {
    let ok:Bool
    let transcript:String?
    let reply:String?
    let audio:String?
    let model:String?
    let error:String?
}

@MainActor
final class WatchVoiceCall:NSObject,ObservableObject,AVAudioPlayerDelegate {
    static let shared=WatchVoiceCall()
    @Published var active=false
    @Published var status="Choose how to call him."
    @Published var heard=""
    @Published var said=""
    @Published var provider:WatchVoiceProvider = .local

    private let engine=AVAudioEngine()
    private let output=AVAudioPlayerNode()
    private var socket:URLSessionWebSocketTask?
    private var localPlayer:AVAudioPlayer?
    private var localChunks=[Data]()
    private var localSpeaking=false
    private var localSilence=0.0
    private var localBusy=false
    private var started=Date()
    private var clientID=""
    private var baseInstructions=""
    private var inputTranscript=""
    private var outputTranscript=""
    private var receiveTask:Task<Void,Never>?
    private var heartbeatTask:Task<Void,Never>?

    func start(_ selected:WatchVoiceProvider) async {
        guard !active else { return }
        provider=selected;status="Connecting…";heard="";said="";started=Date()
        clientID="watch-voice-\(Int(Date().timeIntervalSince1970))"
        do {
            let allowed=await microphonePermission()
            guard allowed else { throw NSError(domain:"VintosWatch",code:1,userInfo:[NSLocalizedDescriptionKey:"Microphone permission is off."]) }
            let token=try await WatchAPI.shared.voiceToken(provider:selected.rawValue)
            if let error=token.error,!error.isEmpty { throw NSError(domain:"VintosWatch",code:2,userInfo:[NSLocalizedDescriptionKey:error]) }
            baseInstructions=token.instructions
            try configureAudio()
            active=true;VintosModel.shared.reaction = .listening
            if selected == .local {
                try startInput()
                status="Listening · Vintos Local"
                try? await WatchAPI.shared.localHeartbeat()
                startHeartbeat()
            } else {
                try await connectRealtime(token:token.token,provider:selected)
                try startInput()
                status="Listening · \(selected.title)"
            }
            WKInterfaceDevice.current().play(.start)
        } catch {
            stopAudio();active=false;status=error.localizedDescription
            VintosModel.shared.reaction = .present;WKInterfaceDevice.current().play(.failure)
        }
    }

    func stop() {
        guard active else { return }
        active=false;receiveTask?.cancel();receiveTask=nil
        heartbeatTask?.cancel();heartbeatTask=nil
        socket?.cancel(with:.normalClosure,reason:nil);socket=nil
        stopAudio();localChunks=[];localSpeaking=false;localSilence=0;localBusy=false
        let duration=Int(Date().timeIntervalSince(started));let p=provider.rawValue;let id=clientID
        Task {
            if provider == .local { try? await WatchAPI.shared.localEnd() }
            try? await WatchAPI.shared.voiceEnd(provider:p,clientID:id,duration:duration)
        }
        VintosModel.shared.reaction = .present;status="Call ended."
        WKInterfaceDevice.current().play(.stop)
    }

    private func microphonePermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { continuation.resume(returning:$0) }
        }
    }

    private func configureAudio() throws {
        let session=AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord,mode:.voiceChat,options:[.allowBluetoothHFP])
        try session.setActive(true)
        if !engine.attachedNodes.contains(output) { engine.attach(output) }
        let format=AVAudioFormat(commonFormat:.pcmFormatFloat32,sampleRate:24000,channels:1,interleaved:false)!
        engine.connect(output,to:engine.mainMixerNode,format:format)
        try engine.start();output.play()
    }

    private func startInput() throws {
        let input=engine.inputNode
        input.removeTap(onBus:0)
        input.installTap(onBus:0,bufferSize:4096,format:nil) { [weak self] buffer,_ in
            guard let self,let converted=self.convert(buffer) else { return }
            let rms=self.rms(converted)
            Task { @MainActor in
                guard self.active else { return }
                if self.provider == .local { self.consumeLocal(converted,rms:rms) }
                else { await self.sendRealtime(converted) }
            }
        }
    }

    nonisolated private func convert(_ input:AVAudioPCMBuffer)->Data? {
        guard let target=AVAudioFormat(commonFormat:.pcmFormatFloat32,sampleRate:24000,channels:1,interleaved:false),
              let converter=AVAudioConverter(from:input.format,to:target) else { return nil }
        let capacity=AVAudioFrameCount((Double(input.frameLength)*24000/input.format.sampleRate).rounded(.up)+8)
        guard let out=AVAudioPCMBuffer(pcmFormat:target,frameCapacity:capacity) else { return nil }
        var supplied=false;var error:NSError?
        converter.convert(to:out,error:&error) { _,state in
            if supplied { state.pointee = .noDataNow;return nil }
            supplied=true;state.pointee = .haveData;return input
        }
        guard error == nil,let channel=out.floatChannelData?[0] else { return nil }
        var pcm=[Int16]();pcm.reserveCapacity(Int(out.frameLength))
        for index in 0..<Int(out.frameLength) {
            let sample=max(-1,min(1,channel[index]));pcm.append(Int16(sample < 0 ? sample*32768:sample*32767))
        }
        return pcm.withUnsafeBytes { Data($0) }
    }

    nonisolated private func rms(_ data:Data)->Float {
        data.withUnsafeBytes { raw in
            let samples=raw.bindMemory(to:Int16.self);guard !samples.isEmpty else { return 0 }
            var sum:Double=0;for sample in samples { let v=Double(sample)/32768;sum += v*v }
            return Float(sqrt(sum/Double(samples.count)))
        }
    }

    private func consumeLocal(_ data:Data,rms:Float) {
        guard !localBusy else { return }
        let seconds=Double(data.count/2)/24000
        if rms > 0.014 {
            localSpeaking=true;localSilence=0;localChunks.append(data);VintosModel.shared.reaction = .listening
        } else if localSpeaking {
            localChunks.append(data);localSilence += seconds
            if localSilence >= 0.8 {
                let audio=localChunks.reduce(into:Data()){$0.append($1)}
                localChunks=[];localSpeaking=false;localSilence=0;localBusy=true
                VintosModel.shared.reaction = .thinking;status="He’s answering…"
                Task { await sendLocalTurn(audio) }
            }
        }
    }

    private func sendLocalTurn(_ audio:Data) async {
        do {
            let framing=(try? await WatchAPI.shared.voiceFraming()) ?? ""
            let result=try await WatchAPI.shared.localTurn(audio:audio.base64EncodedString(),instructions:baseInstructions,framing:framing)
            guard result.ok else { throw NSError(domain:"VintosWatch",code:3,userInfo:[NSLocalizedDescriptionKey:result.error ?? "Local call failed."]) }
            heard=result.transcript ?? "";said=result.reply ?? ""
            if let encoded=result.audio,let data=Data(base64Encoded:encoded) { playLocal(data) }
            try? await WatchAPI.shared.voiceLedger(gloria:heard,vintos:said,provider:"local",clientID:clientID)
        } catch { status=error.localizedDescription;WKInterfaceDevice.current().play(.failure) }
        localBusy=false
        if active { VintosModel.shared.reaction = .listening;status="Listening · Vintos Local" }
    }

    private func connectRealtime(token:String,provider selected:WatchVoiceProvider) async throws {
        guard !token.isEmpty else { throw NSError(domain:"VintosWatch",code:4,userInfo:[NSLocalizedDescriptionKey:"The voice token was empty."]) }
        let url=URL(string:selected == .openai ? "wss://api.openai.com/v1/realtime?model=gpt-realtime":"wss://api.x.ai/v1/realtime?model=grok-voice-latest")!
        let protocols = selected == .openai
            ? ["realtime", "openai-insecure-api-key.\(token)"]
            : ["xai-client-secret.\(token)"]
        let task=URLSession(configuration:.default).webSocketTask(with:url,protocols:protocols);socket=task;task.resume()
        if selected == .grok {
            let update:[String:Any] = ["type":"session.update","session":["voice":"lux","instructions":baseInstructions,
                "turn_detection":["type":"server_vad","prefix_padding_ms":300,"silence_duration_ms":800,"idle_timeout_ms":20000],
                "audio":["input":["format":["type":"audio/pcm","rate":24000],"transcription":["model":"grok-transcribe"]],
                         "output":["format":["type":"audio/pcm","rate":24000]]]]]
            let encoded=try JSONSerialization.data(withJSONObject:update)
            try await task.send(.data(encoded))
        }
        receiveTask=Task { [weak self] in await self?.receiveLoop() }
    }

    private func startHeartbeat() {
        heartbeatTask?.cancel()
        heartbeatTask=Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for:.seconds(10))
                guard let self,self.active,self.provider == .local else { return }
                try? await WatchAPI.shared.localHeartbeat()
            }
        }
    }

    private func sendRealtime(_ pcm:Data) async {
        guard let socket else { return }
        let payload:[String:Any] = ["type":"input_audio_buffer.append","audio":pcm.base64EncodedString()]
        guard let data=try? JSONSerialization.data(withJSONObject:payload) else { return }
        try? await socket.send(.data(data))
    }

    private func receiveLoop() async {
        while active,let socket {
            do {
                let message=try await socket.receive();let data:Data
                switch message { case .data(let value):data=value;case .string(let value):data=Data(value.utf8);@unknown default:continue }
                guard let json=try JSONSerialization.jsonObject(with:data) as? [String:Any],let type=json["type"] as? String else { continue }
                if type == "response.output_audio.delta",let raw=json["delta"] as? String,let pcm=Data(base64Encoded:raw) {
                    VintosModel.shared.reaction = .speaking;playPCM(pcm)
                } else if type.contains("input_audio_transcription"),let text=(json["transcript"] ?? json["delta"]) as? String {
                    inputTranscript = type.hasSuffix("completed") ? text:inputTranscript+text;heard=inputTranscript
                } else if type.contains("output_audio_transcript"),let text=(json["transcript"] ?? json["delta"]) as? String {
                    outputTranscript = type.hasSuffix("done") ? text:outputTranscript+text;said=outputTranscript
                } else if type == "response.created" { VintosModel.shared.reaction = .thinking;status="He’s answering…" }
                else if type == "response.done" {
                    try? await WatchAPI.shared.voiceLedger(gloria:inputTranscript,vintos:outputTranscript,provider:provider.rawValue,clientID:clientID)
                    inputTranscript="";outputTranscript="";VintosModel.shared.reaction = .listening;status="Listening · \(provider.title)"
                }
            } catch { if active { status="Call connection ended.";stop() };break }
        }
    }

    private func playPCM(_ data:Data) {
        let format=AVAudioFormat(commonFormat:.pcmFormatFloat32,sampleRate:24000,channels:1,interleaved:false)!
        let count=data.count/2;guard let buffer=AVAudioPCMBuffer(pcmFormat:format,frameCapacity:AVAudioFrameCount(count)),let target=buffer.floatChannelData?[0] else { return }
        buffer.frameLength=AVAudioFrameCount(count)
        data.withUnsafeBytes { raw in let source=raw.bindMemory(to:Int16.self);for i in 0..<count { target[i]=Float(source[i])/32768 } }
        output.scheduleBuffer(buffer)
    }

    private func playLocal(_ data:Data) {
        do { localPlayer=try AVAudioPlayer(data:data);localPlayer?.delegate=self;VintosModel.shared.reaction = .speaking;localPlayer?.play() }
        catch { status="His reply arrived, but the Watch could not play it." }
    }

    nonisolated func audioPlayerDidFinishPlaying(_ player:AVAudioPlayer,successfully flag:Bool) {
        Task { @MainActor in if self.active { VintosModel.shared.reaction = .listening;self.status="Listening · \(self.provider.title)" } }
    }

    private func stopAudio() {
        engine.inputNode.removeTap(onBus:0);output.stop();engine.stop();localPlayer?.stop();localPlayer=nil
        try? AVAudioSession.sharedInstance().setActive(false,options:.notifyOthersOnDeactivation)
    }
}

struct VoiceCallView:View {
    @StateObject private var call=WatchVoiceCall.shared
    @ObservedObject private var vintos=VintosModel.shared
    var body:some View {
        ScrollView {
            VStack(spacing:10) {
                VintosOrbView(reaction:vintos.reaction)
                Text(call.status).font(.caption).multilineTextAlignment(.center)
                if call.active {
                    Button("End call",role:.destructive){call.stop()}.handGestureShortcut(.primaryAction)
                } else {
                    ForEach(WatchVoiceProvider.allCases) { provider in
                        Button(provider.title){Task{await call.start(provider)}}
                    }
                }
                if !call.heard.isEmpty { Text("You: \(call.heard)").font(.caption2) }
                if !call.said.isEmpty { Text("Vintos: \(call.said)").font(.caption2) }
            }.padding(.horizontal,4)
        }.navigationTitle("Call")
    }
}
