import AVFoundation
import AVKit
import SwiftUI

// The portrait is visual-only. Its source movie contains an AAC track even though
// it is muted; keep that track out of the visual player so the song owns audio.
@MainActor
func reactionVideoItem(_ url:URL) async throws -> AVPlayerItem {
    let asset=AVURLAsset(url:url)
    let duration=try await asset.load(.duration)
    guard let source=try await asset.loadTracks(withMediaType:.video).first else {
        throw URLError(.cannotDecodeContentData)
    }
    let composition=AVMutableComposition()
    guard let track=composition.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid) else {
        throw URLError(.cannotDecodeContentData)
    }
    try track.insertTimeRange(CMTimeRange(start:.zero,duration:duration),of:source,at:.zero)
    track.preferredTransform=try await source.load(.preferredTransform)
    return AVPlayerItem(asset:composition)
}

@MainActor
final class ReactionClipPlayer: ObservableObject {
    let player = AVPlayer()
    private var endObserver: NSObjectProtocol?
    private var currentName = ""
    private var loadTask:Task<Void,Never>?

    init() {
        player.isMuted = true
        player.actionAtItemEnd = .none
        endObserver = NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime, object: nil, queue: .main
        ) { [weak player] note in
            guard let player, note.object as? AVPlayerItem === player.currentItem else { return }
            player.seek(to: .zero)
            player.play()
        }
    }

    func show(_ reaction: VintosReaction) {
        let name = reaction.clipName
        guard name != currentName || player.currentItem == nil else { player.play(); return }
        loadTask?.cancel()
        currentName = name
        player.replaceCurrentItem(with: nil)
        guard !name.isEmpty,
              let url = Bundle.main.url(forResource: name, withExtension: "mp4") else { return }
        loadTask=Task { [weak self] in
            // Keep the original visual playback if the composition cannot be read.
            let item=(try? await reactionVideoItem(url)) ?? AVPlayerItem(url:url)
            guard !Task.isCancelled, let self, self.currentName == name else { return }
            self.player.replaceCurrentItem(with:item)
            self.player.play()
        }
    }

    func pause() { loadTask?.cancel(); player.pause() }

    deinit {
        if let endObserver { NotificationCenter.default.removeObserver(endObserver) }
    }
}

struct ReactionClipView: View {
    let reaction: VintosReaction
    @StateObject private var clip = ReactionClipPlayer()

    var body: some View {
        VideoPlayer(player: clip.player)
            .disabled(true)
            .onAppear { clip.show(reaction) }
            .onChange(of: reaction) { _, next in clip.show(next) }
            .onDisappear { clip.pause() }
    }
}
