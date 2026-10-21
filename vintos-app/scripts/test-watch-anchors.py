#!/usr/bin/env python3
"""Run the actual Swift drain/anchor persistence code with offline HealthKit/network fakes."""
from pathlib import Path
import tempfile,subprocess
source=(Path(__file__).resolve().parents[1]/'ios/VintosWatch/SensorBridge.swift').read_text()
anchor=source[source.index('    private func anchorKey'):source.index('    private func page(')]
drain=source[source.index('    private func drain('):source.index('    private func samplePayload(')]
api=(Path(__file__).resolve().parents[1]/'ios/VintosWatch/WatchAPI.swift').read_text()
api_types=api[api.index('struct ArrivalSong:'):api.index('actor WatchAPI')]
api_data=api[api.index('    private func data('):api.index('    func landings(')]
api_telemetry=api[api.index('    @discardableResult\n    func telemetry('):api.index('    func arrivalSong(')]
transmit=source[source.index('    private func transmit('):source.index('    /// HealthKit delivers')]
harness=r'''
import Foundation
__API_TYPES__
final class FakeSession {
 var attempts=0;var failAt:Int?
 func data(for request:URLRequest)async throws->(Data,URLResponse) {
  attempts+=1
  let status=attempts==failAt ? 422:200
  let body:[String:Any]=["stored":0,"skipped_stale":64,"live":["on":false]]
  return (try JSONSerialization.data(withJSONObject:body),HTTPURLResponse(url:request.url!,statusCode:status,httpVersion:nil,headerFields:nil)!)
 }
}
actor WatchAPI {
 static let shared=WatchAPI();private let session=FakeSession()
 func configure(failAt:Int?){session.failAt=failAt}
 private func request(_ path:String,method:String="GET",json:Any?=nil)throws->URLRequest{URLRequest(url:URL(string:"https://offline.invalid/"+path)!)}
 __API_DATA__
 __API_TELEMETRY__
}
@MainActor final class SongArrival {static let shared=SongArrival();func receive(_ song:ArrivalSong)async{}}
final class WidgetCenter {static let shared=WidgetCenter();func reloadAllTimelines(){}}
final class HKSampleType { let identifier:String; init(_ id:String){identifier=id} }
final class HKSample { let endDate:Date; let index:Int; init(_ i:Int){index=i;endDate=Date(timeIntervalSince1970:Double(i))} }
final class HKQueryAnchor:NSObject,NSSecureCoding {
 static var supportsSecureCoding:Bool{true};let cursor:Int
 init(_ n:Int){cursor=n};required init?(coder:NSCoder){cursor=coder.decodeInteger(forKey:"cursor")}
 func encode(with coder:NSCoder){coder.encode(cursor,forKey:"cursor")}
}
@MainActor final class VintosModel { static let shared=VintosModel();var status="" }
@MainActor final class Harness {
 var draining=Set<String>(),pending=Set<String>();var rows=[HKSample]();var sent=[[[String:Any]]]();var nextTransmission=0;var lastLiveReply=0;var asleep=false
 func page(_ type:HKSampleType,anchor:HKQueryAnchor?) async throws -> ([HKSample],Int,HKQueryAnchor?) {
  let start=anchor?.cursor ?? 0;let end=min(start+64,rows.count);return (Array(rows[start..<end]),0,HKQueryAnchor(end))
 }
 func samplePayload(_ sample:HKSample)->[String:Any]?{["observed_at":sample.endDate.timeIntervalSince1970,"value":sample.index]}
 func batteryPayload()->[String:Any]{["kind":"battery"]}
 func applyLive(_ live:LiveHeartState){}
 __TRANSMIT__
 __CODE__
 func exercise() async {
  let type=HKSampleType("offline-test-"+UUID().uuidString)
  defer{UserDefaults.standard.removeObject(forKey:anchorKey(type))}
  rows=(0..<130).map(HKSample.init);await WatchAPI.shared.configure(failAt:2)
  await drain(type)
  precondition(sent.map{$0.count}==[64]);precondition(loadAnchor(type)?.cursor==64,"HTTP 422 advanced anchor")
  await WatchAPI.shared.configure(failAt:nil);await drain(type)
  precondition(sent.map{$0.count}==[64,64,2]);precondition(loadAnchor(type)?.cursor==130)
  precondition(sent.flatMap{$0}.compactMap{$0["value"] as? Int}==Array(0..<130),"lost or skipped samples")
  precondition(sent.flatMap{$0}.compactMap{$0["observed_at"] as? Double}==(0..<130).map(Double.init),"sample timestamps changed")
  let restored=Harness();precondition(restored.loadAnchor(type)?.cursor==130,"anchor did not persist across instances")
  let sentCount=sent.count;await drain(type);precondition(sent.count==sentCount,"unchanged anchor sent redundant data")
  let other=HKSampleType(type.identifier+"-other");precondition(loadAnchor(other)==nil,"anchors leaked across types")
  print("PASS 130 samples in 64/64/2 batches; HTTP 422 retains anchor; HTTP 200 stored:0 advances anchor; timestamps preserved; anchors persist per type; unchanged pages do not resend")
 }
}
@main struct Run {static func main() async {await Harness().exercise()}}
'''.replace('__CODE__',anchor+drain).replace('__API_TYPES__',api_types).replace('__API_DATA__',api_data).replace('__API_TELEMETRY__',api_telemetry).replace('__TRANSMIT__',transmit.replace('        WidgetCenter.shared.reloadAllTimelines()', '        WidgetCenter.shared.reloadAllTimelines()\n        sent.append(samples)'))
with tempfile.TemporaryDirectory(prefix='vintos-anchors-') as tmp:
 p=Path(tmp);(p/'test.swift').write_text(harness)
 subprocess.run(['xcrun','swiftc','-module-cache-path',str(p/'modules'),'-parse-as-library',str(p/'test.swift'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
