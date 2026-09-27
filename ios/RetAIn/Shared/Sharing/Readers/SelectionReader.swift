import Foundation

/// Text the user selected on a Safari page: their own choice always wins over the whole page.
struct SelectionReader: SourceReader {
    let name = "selection"
    func claims(_ input: ShareInput) -> Bool { Words.count(input.pageScript?["selection"] as? String) >= Words.min }
    func read(_ input: ShareInput) async -> ReaderResult {
        let res = input.pageScript ?? [:]
        return .text(ShareRead(pageScript: res, text: res["selection"] as? String ?? "", url: input.url, extractor: "selection"))
    }
}
