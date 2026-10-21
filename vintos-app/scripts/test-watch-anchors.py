#!/usr/bin/env python3
"""Run the actual Swift drain/anchor persistence code with offline HealthKit/network fakes."""
from pathlib import Path
import tempfile,subprocess
source=(Path(__file__).resolve().parents[1]/'ios/VintosWatch/SensorBridge.swift').read_text()
anchor=source[source.index('    private func anchorKey'):source.index('    private func page(')]
drain=source[source.index('    private func drain('):source.index('    private func samplePayload(')]
harness=r'''
import Foundation
final class HKSampleType { let identifier:String; init(_ id:String){identifier=id} }
final class HKSample { let endDate:Date; let index:Int; init(_ i:Int){index=i;endDate=Date(timeIntervalSince1970:Double(i))} }
final class HKQueryAnchor:NSObject,NSSecureCoding {
 static var supportsSecureCoding:Bool{true};let cursor:Int
 init(_ n:Int){cursor=n};required init?(coder:NSCoder){cursor=coder.decodeInteger(forKey:"cursor")}
 func encode(with coder:NSCoder){coder.encode(cursor,forKey:"cursor")}
}
@MainActor final class VintosModel { static let shared=VintosModel();var status="" }
@MainActor final class Harness {
 var draining=Set<String>(),pending=Set<String>();var rows=[HKSample]();var sent=[[[String:Any]]]();var failAt:Int?;var attempts=0
 func page(_ type:HKSampleType,anchor:HKQueryAnchor?) async throws -> ([HKSample],Int,HKQueryAnchor?) {
  let start=anchor?.cursor ?? 0;let end=min(start+64,rows.count);return (Array(rows[start..<end]),0,HKQueryAnchor(end))
 }
 func samplePayload(_ sample:HKSample)->[String:Any]?{["observed_at":sample.endDate.timeIntervalSince1970,"value":sample.index]}
 func batteryPayload()->[String:Any]{["kind":"battery"]}
 func transmit(_ samples:[[String:Any]]) async throws {attempts+=1;if attempts==failAt{throw URLError(.notConnectedToInternet)};sent.append(samples)}
 __CODE__
 func exercise() async {
  let type=HKSampleType("offline-test-"+UUID().uuidString)
  defer{UserDefaults.standard.removeObject(forKey:anchorKey(type))}
  rows=(0..<130).map(HKSample.init);failAt=2
  await drain(type)
  precondition(sent.map{$0.count}==[64]);precondition(loadAnchor(type)?.cursor==64,"failed send advanced anchor")
  failAt=nil;await drain(type)
  precondition(sent.map{$0.count}==[64,64,2]);precondition(loadAnchor(type)?.cursor==130)
  precondition(sent.flatMap{$0}.compactMap{$0["value"] as? Int}==Array(0..<130),"lost or skipped samples")
  precondition(sent.flatMap{$0}.compactMap{$0["observed_at"] as? Double}==(0..<130).map(Double.init),"sample timestamps changed")
  let restored=Harness();precondition(restored.loadAnchor(type)?.cursor==130,"anchor did not persist across instances")
  let sentCount=sent.count;await drain(type);precondition(sent.count==sentCount,"unchanged anchor sent redundant data")
  let other=HKSampleType(type.identifier+"-other");precondition(loadAnchor(other)==nil,"anchors leaked across types")
  print("PASS 130 samples in 64/64/2 batches; failed batch retries; timestamps preserved; anchors persist per type; unchanged pages do not resend")
 }
}
@main struct Run {static func main() async {await Harness().exercise()}}
'''.replace('__CODE__',anchor+drain)
with tempfile.TemporaryDirectory(prefix='vintos-anchors-') as tmp:
 p=Path(tmp);(p/'test.swift').write_text(harness)
 subprocess.run(['xcrun','swiftc','-module-cache-path',str(p/'modules'),'-parse-as-library',str(p/'test.swift'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True)
