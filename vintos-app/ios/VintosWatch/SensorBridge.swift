import CoreMotion
import Foundation
import HealthKit
import WatchKit
import WidgetKit

final class SensorBridge:NSObject {
    static let shared=SensorBridge()
    private let health=HKHealthStore(); private let motion=CMMotionActivityManager()
    private var started=false
    private var asleep=false
    private let sleepType=HKObjectType.categoryType(forIdentifier:.sleepAnalysis)
    private let types:[HKQuantityTypeIdentifier]=[.heartRate,.restingHeartRate,.heartRateVariabilitySDNN,
        .respiratoryRate,.appleSleepingWristTemperature,.oxygenSaturation,.timeInDaylight,.environmentalAudioExposure]
    func start() {
        guard !started else{return}; started=true
        WKInterfaceDevice.current().isBatteryMonitoringEnabled=true
        var objects=Set<HKObjectType>(types.compactMap{HKObjectType.quantityType(forIdentifier:$0) as HKObjectType?})
        if let sleepType { objects.insert(sleepType) }
        health.requestAuthorization(toShare:[],read:objects){ok,_ in if ok { self.observe(objects) }}
        if CMMotionActivityManager.isActivityAvailable() {
            motion.startActivityUpdates(to:.main){ activity in guard let activity else{return}; self.postMotion(activity) }
        }
        postBattery()
    }
    private func observe(_ objects:Set<HKObjectType>) {
        for object in objects {
            guard let sample=object as? HKSampleType else{continue}
            let query=HKObserverQuery(sampleType:sample,predicate:nil){[weak self] _,done,error in
                defer{done()}; if error==nil { self?.latest(sample) }
            }
            health.execute(query); health.enableBackgroundDelivery(for:sample,frequency:.immediate){_,_ in}
            latest(sample)
        }
    }
    private func latest(_ type:HKSampleType) {
        let q=HKSampleQuery(sampleType:type,predicate:nil,limit:1,sortDescriptors:[NSSortDescriptor(key:HKSampleSortIdentifierEndDate,ascending:false)]){_,rows,_ in
            guard let sample=rows?.first else{return}
            if let quantity=sample as? HKQuantitySample { self.post(quantity) }
            else if let category=sample as? HKCategorySample { self.postSleep(category) }
        }; health.execute(q)
    }
    private func post(_ sample:HKQuantitySample) {
        let map:[HKQuantityTypeIdentifier:(String,HKUnit)]=[
            .heartRate:("heart_rate",HKUnit.count().unitDivided(by:.minute())),
            .restingHeartRate:("resting_heart_rate",HKUnit.count().unitDivided(by:.minute())),
            .heartRateVariabilitySDNN:("hrv_sdnn",.secondUnit(with:.milli)),
            .respiratoryRate:("respiratory_rate",HKUnit.count().unitDivided(by:.minute())),
            .appleSleepingWristTemperature:("wrist_temperature",.degreeCelsius()),
            .oxygenSaturation:("oxygen_saturation",.percent()),
            .timeInDaylight:("time_in_daylight",.second()),
            .environmentalAudioExposure:("noise_exposure",.decibelAWeightedSoundPressureLevel())]
        guard let id=HKQuantityTypeIdentifier(rawValue:sample.quantityType.identifier) as HKQuantityTypeIdentifier?,let (kind,unit)=map[id] else{return}
        var value=sample.quantity.doubleValue(for:unit)
        // HealthKit's percent unit returns 0...100; the private Aegis contract stores 0...1.
        if id == .oxygenSaturation { value /= 100.0 }
        send([["kind":kind,"value":value,"unit":unit.unitString,"observed_at":iso(sample.endDate)]])
    }
    private func postSleep(_ sample:HKCategorySample) {
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
        send([["kind":"sleep","value":label,"observed_at":iso(sample.endDate)]])
    }
    private func postMotion(_ a:CMMotionActivity) {
        let v=a.automotive ? "automotive":a.running ? "running":a.walking ? "walking":a.cycling ? "cycling":a.stationary ? "stationary":"unknown"
        send([["kind":"motion","value":v,"observed_at":iso(a.startDate)]])
    }
    func postBattery() {
        let d=WKInterfaceDevice.current(); let states:[WKInterfaceDeviceBatteryState:String]=[.charging:"charging",.full:"full",.unplugged:"unplugged",.unknown:"unknown"]
        send([["kind":"battery","value":["level":d.batteryLevel,"state":states[d.batteryState] ?? "unknown"],"observed_at":iso(Date())]])
    }
    private func send(_ samples:[[String:Any]]) { Task { try? await WatchAPI.shared.telemetry(samples,asleep:asleep); WidgetCenter.shared.reloadAllTimelines() } }
    private func iso(_ date:Date)->String { ISO8601DateFormatter().string(from:date) }
}
