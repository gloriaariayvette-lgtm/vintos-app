#!/usr/bin/env python3
"""Exercise the shipped live-session lifecycle with local HealthKit/network fakes."""
from pathlib import Path
import tempfile,subprocess
source=(Path(__file__).resolve().parents[1]/'ios/VintosWatch/SensorBridge.swift').read_text()
code=source[source.index('    private func applyLive('):source.index('    nonisolated func workoutSession(')]
harness=r'''
import Foundation
struct LiveHeartState {let on:Bool;let until:String?}
class HKObjectType {static func workoutType()->HKObjectType{HKObjectType()};static func quantityType(forIdentifier:String)->HKObjectType?{HKObjectType()}}
extension String {static let heartRate="heart"}
class Health {var authorization:((Bool,Error?)->Void)?;func requestAuthorization(toShare:[HKObjectType],read:[HKObjectType],completion:@escaping(Bool,Error?)->Void){authorization=completion}}
class HKWorkoutConfiguration {enum Activity{case other};enum Location{case indoor};var activityType:Activity = .other;var locationType:Location = .indoor}
class HKLiveWorkoutDataSource {init(healthStore:Health,workoutConfiguration:HKWorkoutConfiguration){}}
class HKLiveWorkoutBuilder {var dataSource:HKLiveWorkoutDataSource?;weak var delegate:AnyObject?;var discarded=false;func beginCollection(withStart:Date,completion:(Bool,Error?)->Void){completion(true,nil)};func discardWorkout(){discarded=true}}
class HKWorkoutSession {var delegate:AnyObject?;let collection=HKLiveWorkoutBuilder();var ended=false;init(healthStore:Health,configuration:HKWorkoutConfiguration)throws{};func associatedWorkoutBuilder()->HKLiveWorkoutBuilder{collection};func startActivity(with:Date){};func end(){ended=true}}
class WKApplication {enum State{case active,background};static let instance=WKApplication();static func shared()->WKApplication{instance};var applicationState:State = .background}
@MainActor class VintosModel {static let shared=VintosModel();var status=""}
@MainActor class Harness {
 let health=Health();var workout:HKWorkoutSession?;var builder:HKLiveWorkoutBuilder?;var liveUntil:Date?;var liveTimer:Timer?;var expiryTimer:Timer?;var newestHeart:[String:Any]?;var launchRequested=false;var liveSendRunning=false;var posts=[[[String:Any]]]();var serverOff=false
 func batteryPayload()->[String:Any]{["kind":"battery"]}
 func transmit(_ samples:[[String:Any]])async throws{posts.append(samples);if serverOff{applyLive(LiveHeartState(on:false,until:nil))}}
 __CODE__
 func exercise()async {
  let on=LiveHeartState(on:true,until:ISO8601DateFormatter().string(from:Date().addingTimeInterval(3600)))
  applyLive(on);precondition(workout==nil && health.authorization==nil,"background check-in started a workout")
  launchRequested=true;applyLive(on);health.authorization?(true,nil);try? await Task.sleep(nanoseconds:10_000_000)
  precondition(workout != nil && builder?.dataSource != nil,"iPhone launch did not start the live builder")
  newestHeart=["kind":"heart_rate","value":72,"observed_at":"original-observation"]
  await liveTick();precondition(posts.last?.first?["observed_at"] as? String=="original-observation")
  let session=workout!,collection=builder!;serverOff=true;await liveTick()
  precondition(session.ended && collection.discarded && workout==nil && liveTimer==nil && expiryTimer==nil,"Off failed to end/discard")
  serverOff=false;WKApplication.shared().applicationState = .active
  applyLive(on);health.authorization?(true,nil);try? await Task.sleep(nanoseconds:10_000_000)
  let expired=builder!;liveUntil=Date().addingTimeInterval(-1);await liveTick();precondition(expired.discarded && workout==nil,"expiry failed to discard")
  applyLive(on);let deferred=health.authorization;applyLive(LiveHeartState(on:false,until:nil));deferred?(true,nil);try? await Task.sleep(nanoseconds:10_000_000)
  precondition(workout==nil,"late authorization restarted an Off session")
  applyLive(LiveHeartState(on:true,until:"invalid"));precondition(workout==nil)
  print("PASS background launch rules; live builder; newest HR timestamps; server Off; expiry; discard; authorization/Off race")
 }
}
@main struct Run{static func main()async{await Harness().exercise()}}
'''.replace('__CODE__',code)
with tempfile.TemporaryDirectory(prefix='vintos-live-runtime-') as tmp:
 p=Path(tmp);(p/'test.swift').write_text(harness)
 subprocess.run(['xcrun','swiftc','-module-cache-path',str(p/'modules'),'-parse-as-library',str(p/'test.swift'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
