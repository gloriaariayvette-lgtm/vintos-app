import CoreMotion
import Foundation
import HealthKit
import WatchKit
import WidgetKit

@MainActor
final class SensorBridge:NSObject, HKWorkoutSessionDelegate, HKLiveWorkoutBuilderDelegate {
    static let shared=SensorBridge()
    private let health=HKHealthStore(); private let motion=CMMotionActivityManager()
    private var started=false
    private var asleep=false
    private var sampleTypes=[HKSampleType]()
    private var draining=Set<String>()
    private var pending=Set<String>()
    private var workout:HKWorkoutSession?
    private var builder:HKLiveWorkoutBuilder?
    private var liveUntil:Date?
    private var liveTimer:Timer?
    private var expiryTimer:Timer?
    private var newestHeart:[String:Any]?
    private var liveSendRunning=false
    private var launchRequested=false
    private var nextTransmission=0
    private var lastLiveReply=0
    private let sleepType=HKObjectType.categoryType(forIdentifier:.sleepAnalysis)
    private let types:[HKQuantityTypeIdentifier]=[.heartRate,.restingHeartRate,.heartRateVariabilitySDNN,
        .respiratoryRate,.appleSleepingWristTemperature,.oxygenSaturation,.timeInDaylight,.environmentalAudioExposure]
    func start() {
        guard !started else{return}; started=true
        WKInterfaceDevice.current().isBatteryMonitoringEnabled=true
        var objects=Set<HKObjectType>(types.compactMap{HKObjectType.quantityType(forIdentifier:$0) as HKObjectType?})
        if let sleepType { objects.insert(sleepType) }
        health.requestAuthorization(toShare:[HKObjectType.workoutType()],read:objects){ok,_ in
            Task { @MainActor in if ok { self.observe(objects) } }
        }
        if CMMotionActivityManager.isActivityAvailable() {
            motion.startActivityUpdates(to:.main){ activity in guard let activity else{return}; self.postMotion(activity) }
        }
        postBattery()
    }
    private func observe(_ objects:Set<HKObjectType>) {
        sampleTypes=objects.compactMap{$0 as? HKSampleType}
        for sample in sampleTypes {
            let query=HKObserverQuery(sampleType:sample,predicate:nil){[weak self] _,done,error in
                Task { @MainActor in
                    if error == nil,let self {
                        self.postBattery()
                        for type in self.sampleTypes { await self.drain(type) }
                    }
                    done()
                }
            }
            health.execute(query); health.enableBackgroundDelivery(for:sample,frequency:.immediate){_,_ in}
        }
        checkIn()
    }
    /// Called on each foreground wake as well as initial HealthKit setup.
    func checkIn() {
        postBattery()
        for type in sampleTypes { Task { await drain(type) } }
    }
    private func anchorKey(_ type:HKSampleType)->String { "vintos.health.anchor."+type.identifier }
    private func loadAnchor(_ type:HKSampleType)->HKQueryAnchor? {
        guard let data=UserDefaults.standard.data(forKey:anchorKey(type)) else{return nil}
        return try? NSKeyedUnarchiver.unarchivedObject(ofClass:HKQueryAnchor.self,from:data)
    }
    private func page(_ type:HKSampleType,anchor:HKQueryAnchor?) async throws -> ([HKSample],Int,HKQueryAnchor?) {
        try await withCheckedThrowingContinuation { continuation in
            let query=HKAnchoredObjectQuery(type:type,predicate:nil,anchor:anchor,limit:64){_,rows,deleted,next,error in
                if let error { continuation.resume(throwing:error) }
                else { continuation.resume(returning:(rows ?? [],deleted?.count ?? 0,next)) }
            }
            health.execute(query)
        }
    }
    private func drain(_ type:HKSampleType) async {
        let id=type.identifier
        guard !draining.contains(id) else { pending.insert(id); return }
        draining.insert(id)
        defer { draining.remove(id) }
        do {
            repeat {
                pending.remove(id)
                var anchor=loadAnchor(type)
                while true {
                    let (rows,deleted,next)=try await page(type,anchor:anchor)
                    if rows.isEmpty && deleted == 0 { break }
                    let samples=rows.sorted{$0.endDate < $1.endDate}.compactMap{samplePayload($0)}
                    // The server requires 1...64 rows. A deletion-only page checks in
                    // with battery before committing its anchor; failures leave it retryable.
                    try await transmit(samples.isEmpty ? [batteryPayload()] : samples)
                    if let next {
                        let archived=try NSKeyedArchiver.archivedData(withRootObject:next,requiringSecureCoding:true)
                        UserDefaults.standard.set(archived,forKey:anchorKey(type))
                    }
                    anchor=next
                    if rows.count+deleted < 64 { break }
                }
            } while pending.contains(id)
        } catch {
            VintosModel.shared.status="Watch readings will retry: \(error.localizedDescription)"
        }
    }
    private func samplePayload(_ sample:HKSample)->[String:Any]? {
        if let quantity=sample as? HKQuantitySample { return quantityPayload(quantity) }
        if let category=sample as? HKCategorySample { return sleepPayload(category) }
        return nil
    }
    private func quantityPayload(_ sample:HKQuantitySample)->[String:Any]? {
        let map:[HKQuantityTypeIdentifier:(String,HKUnit)]=[
            .heartRate:("heart_rate",HKUnit.count().unitDivided(by:.minute())),
            .restingHeartRate:("resting_heart_rate",HKUnit.count().unitDivided(by:.minute())),
            .heartRateVariabilitySDNN:("hrv_sdnn",.secondUnit(with:.milli)),
            .respiratoryRate:("respiratory_rate",HKUnit.count().unitDivided(by:.minute())),
            .appleSleepingWristTemperature:("wrist_temperature",.degreeCelsius()),
            .oxygenSaturation:("oxygen_saturation",.percent()),
            .timeInDaylight:("time_in_daylight",.second()),
            .environmentalAudioExposure:("noise_exposure",.decibelAWeightedSoundPressureLevel())]
        guard let id=HKQuantityTypeIdentifier(rawValue:sample.quantityType.identifier) as HKQuantityTypeIdentifier?,let (kind,unit)=map[id] else{return nil}
        var value=sample.quantity.doubleValue(for:unit)
        // HealthKit's percent unit returns 0...100; the private Aegis contract stores 0...1.
        if id == .oxygenSaturation { value /= 100.0 }
        return ["kind":kind,"value":value,"unit":unit.unitString,"observed_at":iso(sample.endDate)]
    }
    private func sleepPayload(_ sample:HKCategorySample)->[String:Any] {
        let value=HKCategoryValueSleepAnalysis(rawValue:sample.value)
        let sleeping=value == .asleepUnspecified || value == .asleepCore || value == .asleepDeep || value == .asleepREM
        // A completed sleep stage is current only when it ended very recently. HealthKit may
        // deliver stages in batches, so this remains an estimate and never claims medical fact.
        asleep=sleeping && sample.endDate.timeIntervalSinceNow > -15*60
        let label:String
        switch value {
        case .awake: label="awake"
        case .asleepCore: label="core"
        case .asleepDeep: label="deep"
        case .asleepREM: label="rem"
        case .asleepUnspecified: label="asleep"
        case .inBed: label="in_bed"
        default: label="unknown"
        }
        return ["kind":"sleep","value":label,"observed_at":iso(sample.endDate)]
    }
    private func postMotion(_ a:CMMotionActivity) {
        let v=a.automotive ? "automotive":a.running ? "running":a.walking ? "walking":a.cycling ? "cycling":a.stationary ? "stationary":"unknown"
        send([["kind":"motion","value":v,"observed_at":iso(a.startDate)]])
    }
    private func batteryPayload()->[String:Any] {
        let d=WKInterfaceDevice.current(); let states:[WKInterfaceDeviceBatteryState:String]=[.charging:"charging",.full:"full",.unplugged:"unplugged",.unknown:"unknown"]
        return ["kind":"battery","value":["level":d.batteryLevel,"state":states[d.batteryState] ?? "unknown"],"observed_at":iso(Date())]
    }
    func postBattery() { send([batteryPayload()]) }
    private func send(_ samples:[[String:Any]]) {
        Task { try? await transmit(samples) }
    }
    private func transmit(_ samples:[[String:Any]]) async throws {
        nextTransmission += 1
        let sequence=nextTransmission
        let reply=try await WatchAPI.shared.telemetry(samples,asleep:asleep)
        if let live=reply.live,sequence > lastLiveReply {
            lastLiveReply=sequence
            applyLive(live)
        }
        if let song=reply.song { await SongArrival.shared.receive(song) }
        WidgetCenter.shared.reloadAllTimelines()
    }
    /// HealthKit delivers the iPhone's startWatchApp request here, including a background launch.
    func handleWorkout(_ configuration:HKWorkoutConfiguration) {
        launchRequested=true
        start()
        postBattery() // Verify the owner's current server request before starting collection.
    }
    private func applyLive(_ live:LiveHeartState) {
        guard live.on else { launchRequested=false; stopLive(); return }
        let parser=ISO8601DateFormatter(); parser.formatOptions=[.withInternetDateTime,.withFractionalSeconds]
        let until=live.until.flatMap{parser.date(from:$0) ?? ISO8601DateFormatter().date(from:$0)}
        guard let until,until > Date() else { stopLive(); return }
        liveUntil=until
        expiryTimer?.invalidate()
        expiryTimer=Timer.scheduledTimer(withTimeInterval:until.timeIntervalSinceNow,repeats:false){_ in
            Task { @MainActor in self.stopLive() }
        }
        guard workout == nil else { return }
        guard launchRequested || WKApplication.shared().applicationState == .active else { return }
        launchRequested=false
        health.requestAuthorization(toShare:[HKObjectType.workoutType()],read:[HKObjectType.quantityType(forIdentifier:.heartRate)!]) { ok,error in
            Task { @MainActor in
                guard ok,self.workout == nil,let until=self.liveUntil,until > Date() else{return}
                self.beginLive()
            }
        }
    }
    private func beginLive() {
        do {
            let configuration=HKWorkoutConfiguration(); configuration.activityType = .other; configuration.locationType = .indoor
            let session=try HKWorkoutSession(healthStore:health,configuration:configuration)
            let collection=session.associatedWorkoutBuilder()
            collection.dataSource=HKLiveWorkoutDataSource(healthStore:health,workoutConfiguration:configuration)
            session.delegate=self; collection.delegate=self
            workout=session; builder=collection
            let now=Date(); session.startActivity(with:now)
            collection.beginCollection(withStart:now){ok,error in
                if !ok { Task { @MainActor in self.liveFailed(error) } }
            }
            liveTimer=Timer.scheduledTimer(withTimeInterval:30,repeats:true){_ in Task { @MainActor in await self.liveTick() } }
        } catch { liveFailed(error) }
    }
    private func liveTick() async {
        guard let until=liveUntil,until > Date() else { stopLive(); return }
        guard !liveSendRunning else{return}
        liveSendRunning=true; defer{liveSendRunning=false}
        // Even before the first sensor result, battery check-ins pick up an immediate Off.
        try? await transmit([newestHeart ?? batteryPayload()])
    }
    private func stopLive() {
        liveUntil=nil; newestHeart=nil
        liveTimer?.invalidate(); liveTimer=nil; expiryTimer?.invalidate(); expiryTimer=nil
        let session=workout; let collection=builder
        workout=nil; builder=nil
        session?.end()
        // Never finishWorkout: this temporary session must not create a saved workout.
        collection?.discardWorkout()
    }
    private func liveFailed(_ error:Error?) {
        stopLive()
        VintosModel.shared.status="Live heart rate could not start: \(error?.localizedDescription ?? "HealthKit collection unavailable")"
    }
    nonisolated func workoutSession(_ workoutSession:HKWorkoutSession,didChangeTo toState:HKWorkoutSessionState,from fromState:HKWorkoutSessionState,date:Date) {
        if toState == .ended { Task { @MainActor in if self.workout === workoutSession { self.stopLive() } } }
    }
    nonisolated func workoutSession(_ workoutSession:HKWorkoutSession,didFailWithError error:Error) {
        Task { @MainActor in if self.workout === workoutSession { self.liveFailed(error) } }
    }
    nonisolated func workoutBuilderDidCollectEvent(_ workoutBuilder:HKLiveWorkoutBuilder) {}
    nonisolated func workoutBuilder(_ workoutBuilder:HKLiveWorkoutBuilder,didCollectDataOf collectedTypes:Set<HKSampleType>) {
        Task { @MainActor in
            guard self.builder === workoutBuilder, let heart=HKObjectType.quantityType(forIdentifier:.heartRate),collectedTypes.contains(heart),
                  let stats=workoutBuilder.statistics(for:heart),let quantity=stats.mostRecentQuantity(),
                  let interval=stats.mostRecentQuantityDateInterval() else{return}
            self.newestHeart=["kind":"heart_rate","value":quantity.doubleValue(for:HKUnit.count().unitDivided(by:.minute())),
                              "unit":"count/min","observed_at":self.iso(interval.end)]
        }
    }
    private func iso(_ date:Date)->String { ISO8601DateFormatter().string(from:date) }
}
