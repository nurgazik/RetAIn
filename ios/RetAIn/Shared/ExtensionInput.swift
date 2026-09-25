import Foundation
import UniformTypeIdentifiers

/// What the host app handed an extension (share sheet or Safari action).
struct ExtensionInput {
    var text: String?
    var url: String?
    var title: String?
    var pageText: String?
    var selection: String?
    var typeLog: [String] = []
    var source: String = "share-ext"

    /// A single shared word is a capture (M5); anything longer is a transform.
    var singleWord: String? {
        guard let t = text?.trimmingCharacters(in: .whitespacesAndNewlines), !t.isEmpty,
              t.count <= 40, !t.contains(" "), pageText == nil else { return nil }
        return t.lowercased().trimmingCharacters(in: .punctuationCharacters)
    }
    var effectiveText: String? {
        if let s = selection, s.count >= 200 { return s }
        if let p = pageText, p.count >= 200 { return p }
        if let t = text, t.count >= 200 { return t }
        return nil
    }

    static func gather(from context: NSExtensionContext?, source: String) async -> ExtensionInput {
        var r = ExtensionInput(source: source)
        for item in (context?.inputItems as? [NSExtensionItem]) ?? [] {
            if let s = item.attributedContentText?.string, !s.isEmpty { r.text = s }
            for provider in item.attachments ?? [] {
                r.typeLog.append(provider.registeredTypeIdentifiers.joined(separator: ","))
                if provider.hasItemConformingToTypeIdentifier(UTType.propertyList.identifier) {
                    if let any = try? await provider.loadItem(forTypeIdentifier: UTType.propertyList.identifier),
                       let dict = any as? [String: Any],
                       let res = dict[NSExtensionJavaScriptPreprocessingResultsKey] as? [String: Any] {
                        r.pageText = res["text"] as? String
                        r.selection = res["selection"] as? String
                        r.url = r.url ?? (res["url"] as? String)
                        r.title = r.title ?? (res["title"] as? String)
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
        return r
    }
}
