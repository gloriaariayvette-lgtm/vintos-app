#!/usr/bin/env ruby
# Adds his CallKit ring (VintosCall.swift, VintosCallPlugin.m) and the app's entitlements to the phone target.
# Safe to run again after `npx cap sync ios`.
require 'xcodeproj'

root = File.expand_path('..', __dir__)
project = Xcodeproj::Project.open(File.join(root, 'ios', 'App', 'App.xcodeproj'))
phone = project.targets.find { |t| t.name == 'Vintos' } or abort 'Vintos target not found'
group = project.main_group.children.find { |g| g.respond_to?(:path) && g.path == 'App' } or abort 'App group not found'

%w[VintosCall.swift VintosCallPlugin.m].each do |name|
  ref = group.files.find { |f| f.path == name } || group.new_file(name)
  phone.source_build_phase.add_file_reference(ref, true) unless phone.source_build_phase.files_references.include?(ref)
end
group.new_file('App.entitlements') unless group.files.find { |f| f.path == 'App.entitlements' }

phone.build_configurations.each do |config|
  config.build_settings['CODE_SIGN_ENTITLEMENTS'] = 'App/App.entitlements'
end
project.save
puts 'CallKit ring configured for target Vintos'
