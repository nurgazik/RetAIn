import Foundation

/// A source switched off (D52, until AD-10's terms revisit). It still claims its links, so
/// they don't fall through to `WebPageReader` and get loaded anyway, but reads nothing: the
/// user is asked to select the text and share that instead (D64: the app has no paste tab).
/// The wrapped reader stays built and tested; switching the source back on is removing this
/// wrapper in `ShareRouter`.
struct PausedReader: SourceReader {
    let reader: SourceReader
    /// The source as the user knows it ("Reddit").
    let source: String
    init(_ reader: SourceReader, source: String) { self.reader = reader; self.source = source }

    var name: String { reader.name + "-paused" }
    func claims(_ input: ShareInput) -> Bool { reader.claims(input) }
    func read(_ input: ShareInput) async -> ReaderResult {
        .unusable(title: "Share the text instead",
                  detail: "RetAIn doesn't open \(source) links. Select the post's text, then share the selection to RetAIn.")
    }
}
