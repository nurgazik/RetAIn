import Foundation
import UIKit

/// X links (D47). X turns embedded web views away (it redirects them to `x-safari-https://`,
/// "open in Safari"), so no page is loaded: the post comes from X's public oEmbed endpoint
/// (free, no login, no rate limit — docs.x.com/x-for-websites/oembed-api). oEmbed cuts long
/// posts at ~280 characters ("…" + a t.co link): the reader keeps what arrives and marks it.
struct XReader: SourceReader {
    let name = "x"
    /// Tests stub this; returns the response body and HTTP status.
    var fetch: (URL) async throws -> (Data, Int) = { url in
        let (data, response) = try await URLSession.shared.data(from: url)
        return (data, (response as? HTTPURLResponse)?.statusCode ?? 0)
    }

    func claims(_ input: ShareInput) -> Bool {
        guard let host = input.webURL?.host?.lowercased() else { return false }
        return ["x.com", "twitter.com"].contains { host == $0 || host.hasSuffix("." + $0) }
    }
    func read(_ input: ShareInput) async -> ReaderResult {
        guard let url = input.webURL, url.path.contains("/status/") else {
            return .unusable(title: "Share a single post", detail: "RetAIn reads one X post at a time. Open the post and share it from there.")
        }
        var q = URLComponents(string: "https://publish.x.com/oembed")!
        q.queryItems = [.init(name: "url", value: url.absoluteString), .init(name: "omit_script", value: "1"), .init(name: "dnt", value: "true")]
        guard let (data, status) = try? await fetch(q.url!) else { return Self.notShown }
        guard status == 200, let res = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let html = res["html"] as? String else {
            return status == 404 ? .unusable(title: "This post isn't public",
                                             detail: "It may be deleted or from a protected account. Copy the post's text and share that instead.")
                                 : Self.notShown
        }
        var text = Self.postText(fromEmbed: html)
        // a cut post ends "… https://t.co/…": drop the link, keep the "…"
        text = text.replacingOccurrences(of: #"\s*https?://t\.co/\S+\s*$"#, with: "", options: .regularExpression)
        let cut = text.hasSuffix("…")
        let words = Words.count(text)
        guard words >= Words.min else {
            return .unusable(title: "A short post", detail: "This post is \(words) words; RetAIn needs about \(Words.min) to work with.")
        }
        let author = res["author_name"] as? String ?? ""
        let handle = (res["author_url"] as? String).flatMap { URL(string: $0)?.lastPathComponent }
        var fields = ["site_name": "X"]
        if !author.isEmpty { fields["byline"] = handle.map { "\(author) (@\($0))" } ?? author }
        return .text(ShareRead(text: text, title: author.isEmpty ? nil : "\(author) on X", url: res["url"] as? String ?? url.absoluteString,
                               sourceFields: fields, extractor: cut ? "x-oembed-cut" : "x-oembed"))
    }

    /// The post's text from the embed markup: the blockquote's <p>, line breaks kept, entities decoded.
    static func postText(fromEmbed html: String) -> String {
        guard let r = html.range(of: #"<p[^>]*>([\s\S]*?)</p>"#, options: .regularExpression) else { return "" }
        let decoded = (try? NSAttributedString(data: Data("<meta charset=utf-8>\(html[r])".utf8),
                                               options: [.documentType: NSAttributedString.DocumentType.html,
                                                         .characterEncoding: String.Encoding.utf8.rawValue],
                                               documentAttributes: nil).string) ?? ""
        return decoded.replacingOccurrences(of: "\u{2028}", with: "\n")      // <br> arrives as a line separator
            .replacingOccurrences(of: #"[ \t]+\n"#, with: "\n", options: .regularExpression)
            .replacingOccurrences(of: #"\n{3,}"#, with: "\n\n", options: .regularExpression)
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static let notShown = ReaderResult.unusable(title: "X didn't give us this post",
                                                detail: "Copy the post's text and share that instead.")
}
