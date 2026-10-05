#!/usr/bin/env ruby
# Adds the versioned SwiftUI watch app and WidgetKit extension to Capacitor's Xcode project.
# Safe to run again after `npx cap sync ios`.
require 'xcodeproj'

root = File.expand_path('..', __dir__)
project_path = File.join(root, 'ios', 'App', 'App.xcodeproj')
project = Xcodeproj::Project.open(project_path)
phone = project.targets.find { |t| t.name == 'Vintos' } or abort 'Vintos target not found'

def add_sources(project, target, relative_dir)
  group = project.main_group.children.find { |g| g.respond_to?(:display_name) && g.display_name == File.basename(relative_dir) }
  group ||= project.main_group.new_group(File.basename(relative_dir), '../' + File.basename(relative_dir))
  group.set_source_tree('<group>')
  group.path = '../' + File.basename(relative_dir)
  group.files.each(&:remove_from_project)
  absolute = File.join(project.project_dir, '..', relative_dir.sub(%r{^ios/}, ''))
  Dir.glob(File.join(absolute, '**', '*')).sort.each do |path|
    next unless File.file?(path)
    ext = File.extname(path)
    next unless ['.swift', '.caf', '.xcassets'].include?(ext)
    rel = path.delete_prefix(absolute + '/')
    ref = group.new_file(rel)
    if ext == '.swift'
      target.source_build_phase.add_file_reference(ref, true) unless target.source_build_phase.files_references.include?(ref)
    else
      target.resources_build_phase.add_file_reference(ref, true) unless target.resources_build_phase.files_references.include?(ref)
    end
  end
end

watch = project.targets.find { |t| t.name == 'VintosWatch' } || project.new_target(:application, 'VintosWatch', :watchos, '11.0')
watch.product_type = 'com.apple.product-type.application'
widget = project.targets.find { |t| t.name == 'VintosWatchWidget' } || project.new_target(:app_extension, 'VintosWatchWidget', :watchos, '11.0')

watch.build_configurations.each do |c|
  c.build_settings.merge!({
    'PRODUCT_BUNDLE_IDENTIFIER'=>'dev.vintos.app.watchkitapp', 'PRODUCT_NAME'=>'VintosWatch',
    'INFOPLIST_FILE'=>'../VintosWatch/Info.plist', 'CODE_SIGN_ENTITLEMENTS'=>'../VintosWatch/VintosWatch.entitlements',
    'DEVELOPMENT_TEAM'=>'LH37Z6K7GP', 'CODE_SIGN_STYLE'=>'Automatic', 'SWIFT_VERSION'=>'5.0',
    'WATCHOS_DEPLOYMENT_TARGET'=>'11.0', 'SDKROOT'=>'watchos', 'TARGETED_DEVICE_FAMILY'=>'4',
    'SKIP_INSTALL'=>'NO', 'MARKETING_VERSION'=>'1.0', 'CURRENT_PROJECT_VERSION'=>'1',
    'VINTOS_WATCH_BASE_URL'=>'https://aegis.tailaa3de5.ts.net:8443', 'VINTOS_WATCH_TOKEN'=>''
  })
end
widget.build_configurations.each do |c|
  c.build_settings.merge!({
    'PRODUCT_BUNDLE_IDENTIFIER'=>'dev.vintos.app.watchkitapp.widget', 'PRODUCT_NAME'=>'VintosWatchWidget',
    'INFOPLIST_FILE'=>'../VintosWatchWidget/Info.plist', 'CODE_SIGN_ENTITLEMENTS'=>'../VintosWatchWidget/VintosWatchWidget.entitlements',
    'DEVELOPMENT_TEAM'=>'LH37Z6K7GP', 'CODE_SIGN_STYLE'=>'Automatic', 'SWIFT_VERSION'=>'5.0',
    'WATCHOS_DEPLOYMENT_TARGET'=>'11.0', 'SDKROOT'=>'watchos', 'TARGETED_DEVICE_FAMILY'=>'4',
    'SKIP_INSTALL'=>'YES', 'APPLICATION_EXTENSION_API_ONLY'=>'YES', 'MARKETING_VERSION'=>'1.0', 'CURRENT_PROJECT_VERSION'=>'1'
  })
end

watch.source_build_phase.files.each(&:remove_from_project)
widget.source_build_phase.files.each(&:remove_from_project)
watch.resources_build_phase.files.each(&:remove_from_project)
widget.resources_build_phase.files.each(&:remove_from_project)
project.files.select { |f| f.parent.nil? && (f.path.to_s.end_with?('.swift') || f.path.to_s.end_with?('.caf')) }.each(&:remove_from_project)
add_sources(project, watch, 'ios/VintosWatch')
add_sources(project, widget, 'ios/VintosWatchWidget')

unless watch.dependencies.any? { |d| d.target == widget }
  watch.add_dependency(widget)
end
plugins = watch.copy_files_build_phases.find { |p| p.name == 'Embed App Extensions' } || watch.new_copy_files_build_phase('Embed App Extensions')
plugins.dst_subfolder_spec = '13'
plugins.add_file_reference(widget.product_reference, true) unless plugins.files_references.include?(widget.product_reference)

unless phone.dependencies.any? { |d| d.target == watch }
  phone.add_dependency(watch)
end
embed = phone.copy_files_build_phases.find { |p| p.name == 'Embed Watch Content' } || phone.new_copy_files_build_phase('Embed Watch Content')
embed.dst_subfolder_spec = '16'
embed.dst_path = '$(CONTENTS_FOLDER_PATH)/Watch'
embed.add_file_reference(watch.product_reference, true) unless embed.files_references.include?(watch.product_reference)

project.save
scheme = Xcodeproj::XCScheme.new
scheme.add_build_target(watch)
scheme.set_launch_target(watch)
scheme.save_as(project_path, 'VintosWatch', true)
puts 'VintosWatch and VintosWatchWidget configured'
