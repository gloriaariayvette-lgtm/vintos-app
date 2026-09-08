//  MultiViewFigure.swift
//
//  He stands where he was put, facing the way he was put, and does not turn to
//  follow you. What changes as you walk around him is WHICH view is playing.
//  Those two things together read as depth; neither alone does.
//
//  Drop into VintosRoom and call `MultiViewFigure.make(...)` where the single
//  billboarded plane is created today. Remove the billboard update for these
//  entities — the yaw is fixed on purpose.

import RealityKit
import AVFoundation
import simd

/// One packed clip (colour left, greyscale matte right) and the direction he
/// faces in it, measured as a bearing from "facing the camera".
struct FigureView {
    let url: URL
    /// 0 = he faces the camera, +/-90 = profile, 180 = his back. Radians.
    let bearing: Float
}

final class MultiViewFigure {

    // Tuned, not guessed: 8 degrees of hysteresis stops the view strobing when
    // you stand near a boundary, and a quarter second cross-fade is long enough
    // to hide the cut between clips that were generated independently and are
    // therefore not frame-synchronised.
    private static let hysteresis: Float = 8 * .pi / 180
    private static let fadeDuration: TimeInterval = 0.25

    /// Set once, on the device, by standing to his left and checking which clip
    /// appears. Do not derive it — the handedness depends on the coordinate
    /// system AND on which way each generated clip actually faces.
    static var bearingSign: Float = 1

    private let root: Entity
    private var planes: [(view: FigureView, entity: ModelEntity, player: AVPlayer)] = []
    private var current: Int = 0
    private var facing: SIMD3<Float>          // horizontal, unit
    private var fadeStart: TimeInterval = 0
    private var fadingFrom: Int? = nil

    // MARK: build

    /// - Parameters:
    ///   - views: the packed clips and their bearings
    ///   - heightMeters: measured head-to-foot of the matte, scaled to 1.80
    ///   - facing: horizontal world direction he is turned toward
    init(views: [FigureView], size: SIMD2<Float>, facing: SIMD3<Float>) {
        self.root = Entity()
        self.facing = normalize(SIMD3(facing.x, 0, facing.z))

        for v in views {
            let player = AVPlayer(url: v.url)
            player.actionAtItemEnd = .none
            NotificationCenter.default.addObserver(
                forName: .AVPlayerItemDidPlayToEndTime,
                object: player.currentItem, queue: .main) { _ in
                    player.seek(to: .zero); player.play()
                }

            // PackedVideo.metal reconstructs colour+opacity from the two halves.
            var material = try! CustomMaterial(
                surfaceShader: .init(named: "packedSurface", in: PackedVideo.library),
                geometryModifier: nil,
                lightingModel: .unlit)
            material.custom.texture = .init(try! .load(named: "placeholder"))
            material.faceCulling = .none
            material.blending = .transparent(opacity: .init(floatLiteral: 1))

            let mesh = MeshResource.generatePlane(width: size.x, height: size.y)
            let entity = ModelEntity(mesh: mesh, materials: [material])
            // plane origin is its centre; lift so his feet sit on the anchor
            entity.position.y = size.y / 2
            entity.isEnabled = false
            root.addChild(entity)
            planes.append((v, entity, player))
        }

        // Yaw locked to his facing. This is the line that stops him pivoting.
        let yaw = atan2(self.facing.x, self.facing.z)
        root.orientation = simd_quatf(angle: yaw, axis: [0, 1, 0])

        if let first = planes.first {
            first.entity.isEnabled = true
            first.player.play()
        }
    }

    var entity: Entity { root }

    // MARK: per-frame

    /// Call from a SceneEvents.Update subscription with the camera's world
    /// position. Everything else follows from where she is standing.
    func update(cameraWorldPosition: SIMD3<Float>, now: TimeInterval) {
        let anchorPos = root.position(relativeTo: nil)
        var toCamera = cameraWorldPosition - anchorPos
        toCamera.y = 0
        guard length_squared(toCamera) > 1e-6 else { return }
        toCamera = normalize(toCamera)

        // Where she stands relative to the way he is turned.
        // 0 = in front of him, +/-pi = behind him.
        let cosA = dot(facing, toCamera)
        let cross = facing.x * toCamera.z - facing.z * toCamera.x
        let bearing = atan2(cross * MultiViewFigure.bearingSign, cosA)

        let best = nearestView(to: bearing)
        if best != current {
            // only switch once past the boundary by the hysteresis margin
            let currentErr = angularDistance(bearing, planes[current].view.bearing)
            let bestErr = angularDistance(bearing, planes[best].view.bearing)
            if currentErr - bestErr > MultiViewFigure.hysteresis {
                beginFade(to: best, at: now)
            }
        }
        advanceFade(now: now)
    }

    private func nearestView(to bearing: Float) -> Int {
        var bestIndex = 0
        var bestErr = Float.greatestFiniteMagnitude
        for (i, p) in planes.enumerated() {
            let e = angularDistance(bearing, p.view.bearing)
            if e < bestErr { bestErr = e; bestIndex = i }
        }
        return bestIndex
    }

    private func angularDistance(_ a: Float, _ b: Float) -> Float {
        var d = abs(a - b).truncatingRemainder(dividingBy: 2 * .pi)
        if d > .pi { d = 2 * .pi - d }
        return d
    }

    // MARK: cross-fade

    private func beginFade(to index: Int, at now: TimeInterval) {
        fadingFrom = current
        current = index
        fadeStart = now
        let incoming = planes[index]
        incoming.entity.isEnabled = true
        // Deliberately NOT seeking to zero: each view keeps its own continuous
        // loop, so returning to a view does not restart him from frame one.
        if incoming.player.rate == 0 { incoming.player.play() }
        setOpacity(index, 0)
    }

    private func advanceFade(now: TimeInterval) {
        guard let from = fadingFrom else { return }
        let t = Float(min(1, (now - fadeStart) / MultiViewFigure.fadeDuration))
        setOpacity(current, t)
        setOpacity(from, 1 - t)
        if t >= 1 {
            planes[from].entity.isEnabled = false
            fadingFrom = nil
        }
    }

    private func setOpacity(_ index: Int, _ value: Float) {
        guard var m = planes[index].entity.model?.materials.first as? CustomMaterial else { return }
        m.blending = .transparent(opacity: .init(floatLiteral: value))
        planes[index].entity.model?.materials = [m]
    }
}
