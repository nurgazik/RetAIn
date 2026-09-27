import Foundation
import UniformTypeIdentifiers

/// What the host app handed an extension (share sheet or Safari action), as it arrived.
/// Nothing is interpreted here: the router's readers (Sharing/Readers/) decide what it means.
struct ShareInput {
    var text: String?                  // shared plain text: a selection in a native app, a note…
    var url: String?                   // a shared link, or the page's own URL from Safari
    var pageScript: [String: Any]?     // Safari's pre-step results (RetAInPage.js), Safari only
    var typeLog: [String] = []
    var source: String = "share-ext"

    /// The shared link when it's a web page (http/https).
    var webURL: URL? {
        guard let s = url, let u = URL(string: s), ["http", "https"].contains(u.scheme?.lowercased() ?? "") else { return nil }
        return u
    }
    /// A single shared word is a capture (M5), not a read.
    var singleWord: String? {
        guard let t = text?.trimmingCharacters(in: .whitespacesAndNewlines), !t.isEmpty,
              t.count <= 40, !t.contains(" "), pageScript == nil else { return nil }
        return t.lowercased().trimmingCharacters(in: .punctuationCharacters)
    }
    /// Metadata only, never content.
    var diagnosticPayload: [String: Any] {
        ["types": typeLog, "textWords": Words.count(text), "pageWords": Words.count(pageScript?["text"] as? String),
         "selectionWords": Words.count(pageScript?["selection"] as? String), "hasUrl": url != nil, "source": source]
    }

    static func gather(from context: NSExtensionContext?, source: String) async -> ShareInput {
        var r = ShareInput(source: source)
        for item in (context?.inputItems as? [NSExtensionItem]) ?? [] {
            if let s = item.attributedContentText?.string, !s.isEmpty { r.text = s }
            for provider in item.attachments ?? [] {
                r.typeLog.append(provider.registeredTypeIdentifiers.joined(separator: ","))
                if provider.hasItemConformingToTypeIdentifier(UTType.propertyList.identifier) {
                    if let any = try? await provider.loadItem(forTypeIdentifier: UTType.propertyList.identifier),
                       let dict = any as? [String: Any],
                       let res = dict[NSExtensionJavaScriptPreprocessingResultsKey] as? [String: Any] {
                        r.pageScript = res
                        r.url = r.url ?? (res["url"] as? String)
                    }
                } else if provider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                    if let any = try? await provider.loadItem(forTypeIdentifier: UTType.plainText.identifier) {
                        if let s = any as? String { r.text = s }
                        else if let d = any as? Data, let s = String(data: d, encoding: .utf8) { r.text = s }
                        else if let a = any as? NSAttributedString { r.text = a.string }
                    }
                } else if provider.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    if let any = try? await provider.loadItem(forTypeIdentifier: UTType.url.identifier),
                       let u = any as? URL { r.url = u.absoluteString }
                }
            }
        }
        r.promoteLinkText()
        return r
    }

    /// Some apps (Facebook) share a link as plain text: text that is only a web address is a link.
    mutating func promoteLinkText() {
        guard url == nil, let t = text?.trimmingCharacters(in: .whitespacesAndNewlines), !t.contains(where: \.isWhitespace),
              let u = URL(string: t), ["http", "https"].contains(u.scheme?.lowercased() ?? ""), u.host != nil else { return }
        url = t
        text = nil
    }
}
