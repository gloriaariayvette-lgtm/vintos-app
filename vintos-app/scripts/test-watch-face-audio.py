#!/usr/bin/env python3
"""Run the actual visual-only portrait composition against bundled clips.

No Watch app launch, network, provider calls, notifications, or audio playback.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'ios/VintosWatch/ReactionClipView.swift').read_text()
start = source.index('@MainActor\nfunc reactionVideoItem')
end = source.index('\n@MainActor\nfinal class ReactionClipPlayer', start)
helper = source[start:end]
check = '''
@main struct Check {
 @MainActor static func main() async throws {
  for name in CommandLine.arguments.dropFirst() {
   let original=AVURLAsset(url:URL(fileURLWithPath:name))
   let item=try await reactionVideoItem(URL(fileURLWithPath:name))
   let audio=try await item.asset.loadTracks(withMediaType:.audio)
   let video=try await item.asset.loadTracks(withMediaType:.video)
   let before=try await original.load(.duration)
   let after=try await item.asset.load(.duration)
   precondition(audio.isEmpty && video.count==1)
   precondition(abs(before.seconds-after.seconds)<0.05)
   print("PASS portrait video and duration preserved without an audio track: " + URL(fileURLWithPath:name).lastPathComponent)
  }
 }
}
'''
with tempfile.TemporaryDirectory(prefix='vintos-face-audio-') as directory:
    scratch = Path(directory)
    swift = scratch / 'Check.swift'
    swift.write_text('import Foundation\nimport AVFoundation\n' + helper + check)
    executable = scratch / 'check'
    subprocess.run(['xcrun', 'swiftc', '-parse-as-library', str(swift), '-o', str(executable)], check=True)
    clips = sorted((root / 'ios/VintosWatch/ReactionClips').glob('*.mp4'))
    assert clips and scratch.is_dir()
    subprocess.run([str(executable), *map(str, clips)], check=True)
