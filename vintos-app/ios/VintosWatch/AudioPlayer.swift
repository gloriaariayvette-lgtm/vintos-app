import AVFoundation
import Foundation

@MainActor
final class AudioPlayer {
    static let shared=AudioPlayer(); private var player:AVPlayer?
    func play(_ url:URL) {
        do {
            let session=AVAudioSession.sharedInstance()
            try session.setCategory(.playback,mode:.default,policy:.longFormAudio)
            try session.setActive(true)
            player=AVPlayer(url:url); player?.play()
        } catch { VintosModel.shared.status="The Watch could not start audio: \(error.localizedDescription)" }
    }
}
