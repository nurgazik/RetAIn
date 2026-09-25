import Foundation

struct Piece: Codable, Identifiable {
    let id: String
    let title: String
    let body: String      // HTML from the server, <p> + <mark data-def="…">
    let label: String
    let attrib: String
    var source: String
    var created: Date
    var latencyMs: Int
    var wordCount: Int { body.replacingOccurrences(of: "<[^>]+>", with: " ", options: .regularExpression).split(whereSeparator: { $0.isWhitespace }).count }
    var markCount: Int { body.components(separatedBy: "<mark").count - 1 }
}

/// Everything the host app handed us, plus a log of what arrived (G1 sub-question b).
struct ExtensionInput {
    var text: String?          // public.plain-text attachment or attributedContentText
    var url: String?           // public.url attachment, or page URL from JS
    var title: String?
    var pageText: String?      // JS preprocessing: article/main/body innerText
    var selection: String?     // JS preprocessing: window.getSelection()
    var typeLog: [String] = [] // registeredTypeIdentifiers per attachment
    var source: String = "share-ext"

    /// What we would actually transform, in priority order.
    var effectiveText: String? {
        if let s = selection, s.count >= 200 { return s }
        if let p = pageText, p.count >= 200 { return p }
        if let t = text, t.count >= 200 { return t }
        return nil
    }
    var summary: String {
        var parts: [String] = []
        parts.append("types: " + (typeLog.isEmpty ? "(none)" : typeLog.joined(separator: " | ")))
        if let t = text { parts.append("text: \(t.count) chars") }
        if let u = url { parts.append("url: \(u)") }
        if let p = pageText { parts.append("pageText: \(p.count) chars") }
        if let s = selection, !s.isEmpty { parts.append("selection: \(s.count) chars") }
        return parts.joined(separator: "\n")
    }
}
