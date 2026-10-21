import AVFoundation
import Foundation
import MediaPlayer
import UIKit
import UserNotifications
import WatchKit

/// His songs. While one plays, his face stays with it (Gloria, 19 October): the orb sings until the song ends, and the
/// Now Playing screen the Watch switches to shows his face as the song's picture, under the song's title.
@MainActor
final class AudioPlayer {
    static let shared=AudioPlayer()
    private var player:AVPlayer?
    private var ended:NSObjectProtocol?
    private var failed:NSObjectProtocol?
    private var itemStatus:NSKeyValueObservation?
    private var playbackStatus:NSKeyValueObservation?
    private var requestID=UUID()

    func play(_ url:URL, title:String?=nil) {
        let id=UUID(); requestID=id
        player?.pause()
        VintosModel.shared.audioStatus="Connecting audio…"
        do {
            let session=AVAudioSession.sharedInstance()
            try session.setCategory(.playback,mode:.default,policy:.longFormAudio)
            // watchOS resolves the output route asynchronously for long-form audio.
            session.activate(options: []) { [weak self] active, error in
                Task { @MainActor in
                    guard let self, self.requestID == id else { return }
                    guard active, error == nil else {
                        self.reportFailure(error?.localizedDescription ?? "No audio output was selected.")
                        return
                    }
                    self.start(url,title:title,id:id)
                }
            }
        } catch { reportFailure(error.localizedDescription) }
    }

    private func start(_ url:URL,title:String?,id:UUID) {
        let item=AVPlayerItem(url:url)
        itemStatus=nil; playbackStatus=nil
        if let ended { NotificationCenter.default.removeObserver(ended) }
        if let failed { NotificationCenter.default.removeObserver(failed) }
        ended=NotificationCenter.default.addObserver(forName:.AVPlayerItemDidPlayToEndTime,object:item,queue:.main) { _ in
            Task { @MainActor in
                guard AudioPlayer.shared.requestID == id else { return }
                AudioPlayer.shared.finished()
            }
        }
        failed=NotificationCenter.default.addObserver(forName:.AVPlayerItemFailedToPlayToEndTime,object:item,queue:.main) { note in
            let message=(note.userInfo?[AVPlayerItemFailedToPlayToEndTimeErrorKey] as? Error)?.localizedDescription ?? "The song could not finish playing."
            Task { @MainActor in
                guard AudioPlayer.shared.requestID == id else { return }
                AudioPlayer.shared.reportFailure(message)
            }
        }
        let playing=AVPlayer(playerItem:item); player=playing
        itemStatus=item.observe(\.status,options:[.initial,.new]) { [weak self] item,_ in
            Task { @MainActor in
                guard let self, self.requestID == id else { return }
                if item.status == .failed { self.reportFailure(item.error?.localizedDescription ?? "The song could not load.") }
            }
        }
        playbackStatus=playing.observe(\.timeControlStatus,options:[.initial,.new]) { [weak self] player,_ in
            Task { @MainActor in
                guard let self, self.requestID == id, item.status != .failed else { return }
                switch player.timeControlStatus {
                case .playing: VintosModel.shared.audioStatus=""; VintosModel.shared.react("singing")
                case .waitingToPlayAtSpecifiedRate: VintosModel.shared.audioStatus="Loading the song…"
                default: break
                }
            }
        }
        nowPlaying(title)
        playing.play()
    }

    private func reportFailure(_ message:String) {
        player?.pause()
        MPNowPlayingInfoCenter.default().nowPlayingInfo=nil
        VintosModel.shared.audioStatus="Could not play this song: \(message)"
        if VintosModel.shared.reaction == .singing { VintosModel.shared.react("present") }
    }

    private func nowPlaying(_ title:String?) {
        var info:[String:Any]=[MPMediaItemPropertyTitle:(title?.isEmpty == false ? title! : "A song from Vintos"),
                                MPMediaItemPropertyArtist:"Vintos"]
        if let face=UIImage(named:"vintos-headshot") {
            info[MPMediaItemPropertyArtwork]=MPMediaItemArtwork(boundsSize:face.size) { _ in face }
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo=info
    }

    private func finished() {
        VintosModel.shared.audioStatus=""
        MPNowPlayingInfoCenter.default().nowPlayingInfo=nil
        if VintosModel.shared.reaction == .singing { VintosModel.shared.react("present") }
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
            AudioPlayer.shared.play(url,title:song.title); WKInterfaceDevice.current().play(.start)
        } else {
            let content = UNMutableNotificationContent()
            content.title = song.title
            content.body = "His newest song, for when you came in."
            content.sound = .default
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
