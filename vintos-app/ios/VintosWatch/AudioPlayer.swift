import AVFoundation
import Foundation
import UserNotifications
import WatchKit

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

/// The bedroom song (Gloria, 17 October). When she comes into the bedroom, Aegis holds his newest song for the Watch
/// and hands it over at the next check-in. Open on her wrist, it plays at once; otherwise the Watch raises its own
/// notification with Play (a local one, no push key needed). Either way it goes first in the list.
@MainActor
final class SongArrival {
    static let shared = SongArrival()
    private let seenKey = "arrivalSongID"

    func receive(_ song: ArrivalSong) async {
        guard UserDefaults.standard.string(forKey: seenKey) != song.id,
              let url = WatchAPI.shared.absolute(song.media_url) else { return }
        UserDefaults.standard.set(song.id, forKey: seenKey)
        VintosModel.shared.react("singing")
        if WKApplication.shared().applicationState == .active {
            AudioPlayer.shared.play(url); WKInterfaceDevice.current().play(.start)
        } else {
            let content = UNMutableNotificationContent()
            content.title = song.title
            content.body = "His newest song, for when you came in."
            content.sound = UNNotificationSound(named: UNNotificationSoundName("vintos.caf"))
            content.categoryIdentifier = "VINTOS_SONG"
            content.threadIdentifier = "vintos"
            content.interruptionLevel = .active
            content.userInfo = ["vintos": ["kind": "song", "media_url": song.media_url,
                                           "message_id": song.id, "reaction": "singing"]]
            try? await UNUserNotificationCenter.current().add(
                UNNotificationRequest(identifier: "arrival-" + song.id, content: content, trigger: nil))
        }
        try? await WatchAPI.shared.tookSong(song.id)
        await VintosModel.shared.refresh()
    }
}
