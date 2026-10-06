import AVFoundation
import AVKit
import SwiftUI

@MainActor
final class ReactionClipPlayer: ObservableObject {
    let player = AVPlayer()
    private var endObserver: NSObjectProtocol?
    private var currentName = ""

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
        guard name != currentName else { player.play(); return }
        currentName = name
        player.replaceCurrentItem(with: nil)
        guard !name.isEmpty,
              let url = Bundle.main.url(forResource: name, withExtension: "mp4") else { return }
        let item = AVPlayerItem(url: url)
        player.replaceCurrentItem(with: item)
        player.play()
    }

    func pause() { player.pause() }

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
