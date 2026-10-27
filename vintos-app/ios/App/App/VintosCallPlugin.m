#import <Foundation/Foundation.h>
#import <Capacitor/Capacitor.h>

// Registers the app's own VintosCall plugin (VintosCall.swift) with Capacitor's bridge.
CAP_PLUGIN(VintosCallPlugin, "VintosCall",
    CAP_PLUGIN_METHOD(configure, CAPPluginReturnPromise);
    CAP_PLUGIN_METHOD(endCall, CAPPluginReturnPromise);
    CAP_PLUGIN_METHOD(ringStop, CAPPluginReturnPromise);
)
