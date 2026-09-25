import Foundation
import UniformTypeIdentifiers

extension ExtensionInput {
    /// Reads every attachment the host app handed over and logs its type identifiers (G1 sub-question b).
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
                        r.typeLog.append("js-preprocessing: root=\(res["root"] ?? "?") text=\((res["text"] as? String)?.count ?? 0)")
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
