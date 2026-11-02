import XCTest
@testable import RetAIn

/// Keyword search over the user's words (App/WordSearch.swift): folding, ranking, fields, forms, typos.
final class WordSearchTests: XCTestCase {
    private func w(_ id: Int, _ word: String, _ def: String = "", note: String? = nil) -> Word {
        var x = Word(id: id, word: word, pos: nil, definition: def, status: "learning", added: "", servings: nil)
        x.note = note
        return x
    }
    private lazy var words = [
        w(1, "bolster", "To support or strengthen."),
        w(2, "bolsterer", "One who bolsters."),
        w(3, "embolster", "x"),
        w(4, "galvanize", "To shock into action.", note: "мобилизовать — like my coach"),
        w(5, "exigency", "An urgent need."),
        w(6, "café", "A small restaurant."),
        w(7, "stoke", "To feed a fire."),
        w(8, "gaze", "To look steadily."),
    ]
    private func ids(_ q: String) -> [Int] { WordSearch.results(words, q).map(\.word.id) }

    func testRankingExactThenPrefixThenContains() {
        XCTAssertEqual(ids("bolster"), [1, 2, 3])
        XCTAssertEqual(ids("bols"), [1, 2, 3])  // two start with it (shorter first), one contains it
    }

    func testCaseAccentsAndSpacesDontMatter() {
        XCTAssertEqual(ids("  CAFE "), [6])
        XCTAssertEqual(ids("Bolster"), [1, 2, 3])
    }

    /// The list (not search): learning then retained, each A–Z regardless of case or the order words were saved.
    func testListIsAlphabeticalWithinEachGroup() {
        var r = w(4, "bolster"); r.status = "retained"
        let g = WordsView.groups([w(1, "zeitgeist"), w(2, "Acumen"), r, w(3, "candor"), w(5, "aplomb")])
        XCTAssertEqual(g.map(\.0), ["learning", "retained"])
        XCTAssertEqual(g[0].1.map(\.word), ["Acumen", "aplomb", "candor", "zeitgeist"])
        XCTAssertEqual(g[1].1.map(\.word), ["bolster"])
    }

    /// D71: the filter keeps one group or both; sorting by when it was saved, newest or oldest first.
    func testFilterAndSortByDateAdded() {
        func d(_ id: Int, _ word: String, _ added: String, _ status: String = "learning") -> Word {
            Word(id: id, word: word, pos: nil, definition: "", status: status, added: added, servings: nil)
        }
        let all = [d(1, "candor", "2026-10-01"), d(2, "acumen", "2026-10-20"), d(3, "bolster", "2026-10-20"),
                   d(4, "zeal", "2026-09-01", "retained")]
        XCTAssertEqual(WordsView.groups(all, show: .retained).map(\.0), ["retained"])
        XCTAssertEqual(WordsView.groups(all, show: .learning).map(\.0), ["learning"])
        XCTAssertEqual(WordsView.groups(all, sort: .newest)[0].1.map(\.word), ["bolster", "acumen", "candor"])  // same day: later id first
        XCTAssertEqual(WordsView.groups(all, sort: .oldest)[0].1.map(\.word), ["candor", "acumen", "bolster"])
        XCTAssertEqual(WordsView.groups(all).map(\.0), ["learning", "retained"])
        XCTAssertTrue(WordsView.groups(all.filter { $0.status == "learning" }, show: .retained).isEmpty)
    }

    func testInflectedFormsFindTheWord() {
        XCTAssertEqual(ids("bolstered").first, 1)
        XCTAssertEqual(ids("exigencies").first, 5)
        XCTAssertEqual(ids("stoking").first, 7)
        XCTAssertFalse(ids("gazette").contains(8))  // not an inflection
    }

    func testNoteAndMeaningMatchSayWhere() {
        let note = WordSearch.results(words, "мобилизовать")
        XCTAssertEqual(note.map(\.word.id), [4]); XCTAssertEqual(note.first?.field, .note)
        let meaning = WordSearch.results(words, "urgent")
        XCTAssertEqual(meaning.map(\.word.id), [5]); XCTAssertEqual(meaning.first?.snippet, "An urgent need.")
    }

    func testEveryTermMustMatch() {
        XCTAssertEqual(ids("shock action"), [4])
        XCTAssertEqual(ids("shock fire"), [])
    }

    func testNearMissSpellingsComeLast() {
        XCTAssertEqual(ids("galvanise"), [4])  // one letter off
        XCTAssertEqual(ids("exigensy"), [5])
        XCTAssertEqual(ids("stake"), [7])      // short words: one letter off
        XCTAssertEqual(ids("stack"), [])       // two letters off a short word: not a match
    }

    func testExactAndEmpty() {
        XCTAssertTrue(WordSearch.hasExact(words, " Bolster "))
        XCTAssertFalse(WordSearch.hasExact(words, "bolsters"))
        XCTAssertEqual(ids("   "), [])
    }
}
