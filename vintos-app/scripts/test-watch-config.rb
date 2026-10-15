#!/usr/bin/env ruby
require 'xcodeproj'
require 'open3'
project=Xcodeproj::Project.open(File.expand_path('../ios/App/App.xcodeproj',__dir__))
watch=project.targets.find{|target|target.name=='VintosWatch'}
phase=watch.shell_script_build_phases.find{|item|item.name=='Validate Watch connection configuration'}
abort 'Missing Watch build guard' unless phase && phase.show_env_vars_in_log=='0'
[[nil,false],['test-only',true]].each do |token,success|
  out,err,status=Open3.capture3({'VINTOS_WATCH_TOKEN'=>token},'/bin/sh','-c',phase.shell_script)
  abort 'Wrong Watch credential guard outcome' unless status.success? == success
  abort 'Credential echoed' if (out+err).include?('test-only')
end
puts 'PASS actual Xcode Watch guard blocks missing credentials, accepts configured builds, and hides the build environment'
