import XCTest
@testable import RetAIn

/// Word cards (D48): the API row decodes with its card, old widget caches still decode, the
/// reader finds the user's word from its printed form, and the widget link round-trips.
final class WordCardTests: XCTestCase {
    func testServerRowWithCardDecodes() throws {
        let json = """
        {"id": 4, "word": "ran", "pos": "verb", "definition": "To move quickly.", "status": "learning",
         "added": "2026-09-27", "lexicon_id": 9, "servings": 2, "unverified": false,
         "card": {"headword": "run", "source": "wiktionary", "source_url": "https://en.wiktionary.org/wiki/run",
                  "ipa": [{"ipa": "/ɹʌn/", "tags": ["US"]}],
                  "senses": [{"pos": "verb", "gloss": "To move quickly.", "tags": [], "examples": ["She ran."]},
                             {"pos": "noun", "gloss": "An act of running.", "tags": ["countable"], "examples": []}]}}
        """
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        let w = try d.decode(Word.self, from: Data(json.utf8))
        XCTAssertEqual(w.card?.headword, "run")
        XCTAssertEqual(w.card?.sourceUrl, "https://en.wiktionary.org/wiki/run")
        XCTAssertEqual(w.firstDefinition, "To move quickly.")
        XCTAssertEqual(w.card?.senses.count, 2)
        XCTAssertFalse(w.isUnverified)
    }

    /// The widget reads words.json written by an older build (no card, no unverified).
    func testOldCachedWordDecodes() throws {
        let json = #"[{"id": 1, "word": "bolster", "definition": "to support", "status": "learning", "added": "2026-09-01"}]"#
        let w = try JSONDecoder().decode([Word].self, from: Data(json.utf8))[0]
        XCTAssertNil(w.card)
        XCTAssertEqual(w.firstDefinition, "to support")
        XCTAssertFalse(w.isUnverified)
    }

    func testReaderMatchesPrintedFormToTheWord() {
        let words = [Word(id: 1, word: "bolster", pos: nil, definition: "", status: "learning", added: "", servings: nil),
                     Word(id: 2, word: "bolsterer", pos: nil, definition: "", status: "learning", added: "", servings: nil)]
        XCTAssertEqual(ReaderView.match("Bolstered", in: words)?.id, 1)
        XCTAssertEqual(ReaderView.match("bolsterer", in: words)?.id, 2)  // exact match first
        XCTAssertNil(ReaderView.match("ubiquitous", in: words))
    }

    func testWidgetLinkRoundTrips() {
        XCTAssertEqual(WordLink.id(from: WordLink.url(42)), 42)
        XCTAssertNil(WordLink.id(from: URL(string: "https://example.com/word/42")!))
    }
}
