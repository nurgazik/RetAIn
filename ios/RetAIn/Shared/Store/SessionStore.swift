import Foundation
import Security

/// Session token in the keychain, shared with the extensions through the app group
/// (an app group doubles as a keychain access group). Server URL override in shared defaults.
enum SessionStore {
    static let appGroup = "group.com.retain.app"
    static let defaults = UserDefaults(suiteName: appGroup) ?? .standard
    private static let account = "session-token"

    static var serverURL: URL {
        if let s = defaults.string(forKey: "serverURL"), let u = URL(string: s) { return u }
        let s = (Bundle.main.object(forInfoDictionaryKey: "RETAIN_SERVER") as? String) ?? "https://rays-mac-mini.tailb493b3.ts.net"
        return URL(string: s)!
    }
    static func setServerURL(_ s: String?) { defaults.set(s?.isEmpty == false ? s : nil, forKey: "serverURL") }

    static var token: String? {
        get {
            if let t = embeddedDevToken { return t }
            #if targetEnvironment(simulator)
            // The simulator does not share keychain items between an app and its extensions;
            // fall back to the app-group defaults so extension flows can be tested there.
            return defaults.string(forKey: "sim-session-token")
            #else
            var q = query; q[kSecReturnData as String] = true; q[kSecMatchLimit as String] = kSecMatchLimitOne
            var out: AnyObject?
            guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess, let d = out as? Data else { return nil }
            return String(data: d, encoding: .utf8)
            #endif
        }
        set {
            #if targetEnvironment(simulator)
            defaults.set(newValue, forKey: "sim-session-token")
            #else
            SecItemDelete(query as CFDictionary)
            guard let newValue, let d = newValue.data(using: .utf8) else { return }
            var q = query; q[kSecValueData as String] = d
            q[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
            SecItemAdd(q as CFDictionary, nil)
            #endif
        }
    }
    static var isSignedIn: Bool { token != nil }

    /// Debug builds only: a token baked in at build time (`xcodebuild … RETAIN_DEV_TOKEN=…`) lets a
    /// device test run without the app-group keychain (free personal teams can't sign App Groups).
    static var embeddedDevToken: String? {
        #if DEBUG
        let t = (Bundle.main.object(forInfoDictionaryKey: "RETAIN_DEV_TOKEN") as? String) ?? ""
        return t.isEmpty || t.hasPrefix("$(") ? nil : t
        #else
        return nil
        #endif
    }

    private static var query: [String: Any] {
        var q: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                kSecAttrService as String: "com.retain.app",
                                kSecAttrAccount as String: account]
        #if !targetEnvironment(simulator)
        q[kSecAttrAccessGroup as String] = appGroup   // simulator keychain ignores access groups
        #endif
        return q
    }
}
