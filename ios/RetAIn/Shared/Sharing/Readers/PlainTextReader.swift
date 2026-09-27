import Foundation

/// Text shared from any app (a selection in a native app, copied text, a note).
struct PlainTextReader: SourceReader {
    let name = "plain-text"
    func claims(_ input: ShareInput) -> Bool { Words.count(input.text) >= Words.min }
    func read(_ input: ShareInput) async -> ReaderResult {
        .text(ShareRead(text: input.text ?? "", url: input.url, extractor: "plain-text"))
    }
}
