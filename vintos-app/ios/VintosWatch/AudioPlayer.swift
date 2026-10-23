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
    static let shared=AudioPlayer(); private var player:AVPlayer?; private var ended:NSObjectProtocol?
    /// The song now playing, so its end can be told to Aegis as the same song (Gloria, 22 October: he should know when
    /// the Watch played a song of his).
    private var current:(url:URL,title:String?,id:String?)?
    func play(_ url:URL, title:String?=nil, songID:String?=nil, via:String="watch list") {
        do {
            let session=AVAudioSession.sharedInstance()
            try session.setCategory(.playback,mode:.default,policy:.longFormAudio)
            try session.setActive(true)
            let item=AVPlayerItem(url:url)
            if let ended { NotificationCenter.default.removeObserver(ended) }
            ended=NotificationCenter.default.addObserver(forName:.AVPlayerItemDidPlayToEndTime,object:item,queue:.main) { _ in
                Task { @MainActor in AudioPlayer.shared.finished() }
            }
            player=AVPlayer(playerItem:item); player?.play()
            VintosModel.shared.react("singing")
            nowPlaying(title)
            current=(url,title,songID)
            Task { try? await WatchAPI.shared.songPlayed(event:"started",mediaURL:url.absoluteString,title:title,id:songID,via:via) }
        } catch { VintosModel.shared.status="The Watch could not start audio: \(error.localizedDescription)" }
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
        if let song=current {
            Task { try? await WatchAPI.shared.songPlayed(event:"finished",mediaURL:song.url.absoluteString,title:song.title,id:song.id,via:"") }
            current=nil
        }
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
            AudioPlayer.shared.play(url,title:song.title,songID:song.id,via:"arrived with the app open"); WKInterfaceDevice.current().play(.start)
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
