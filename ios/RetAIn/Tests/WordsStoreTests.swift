import XCTest
@testable import RetAIn

/// The widget's words of the day: repeatable per day, learning only, at most five.
final class WordsStoreTests: XCTestCase {
    private func word(_ id: Int, _ status: String = "learning") -> Word {
        Word(id: id, word: "w\(id)", pos: nil, definition: "d\(id)", status: status, added: "2026-09-27", servings: nil)
    }
    private let many = Array(1...30)

    func testSameDaySameWords() {
        let words = many.map { word($0) }
        XCTAssertEqual(WordsStore.todaysWords(from: words, day: "2026-09-27"),
                       WordsStore.todaysWords(from: words.reversed(), day: "2026-09-27"))
    }
    func testDifferentDayDifferentWords() {
        let words = many.map { word($0) }
        XCTAssertNotEqual(WordsStore.todaysWords(from: words, day: "2026-09-27").map(\.id),
                          WordsStore.todaysWords(from: words, day: "2026-09-28").map(\.id))
    }
    func testLearningOnlyAndAtMostFive() {
        let words = many.map { word($0, $0 % 2 == 0 ? "learning" : "retained") } + [word(99, "archived")]
        let today = WordsStore.todaysWords(from: words, day: "2026-09-27")
        XCTAssertEqual(today.count, 5)
        XCTAssertTrue(today.allSatisfy { $0.status == "learning" })
    }
    func testFewerThanFiveGivesAll() {
        let words = [word(1), word(2), word(3, "retained")]
        XCTAssertEqual(Set(WordsStore.todaysWords(from: words, day: "2026-09-27").map(\.id)), [1, 2])
    }
    func testCacheRoundTripAndPosition() {
        let saved = WordsStore.load()
        defer { if let saved { WordsStore.replaceAll(saved) } }
        let words = [word(1), word(2)]
        WordsStore.replaceAll(words)
        XCTAssertEqual(WordsStore.load(), words)

        let day = "2000-01-01"
        XCTAssertEqual(WordsStore.position(day: "1999-12-31"), 0)
        WordsStore.advance(day: day, count: 2); XCTAssertEqual(WordsStore.position(day: day), 1)
        WordsStore.advance(day: day, count: 2); XCTAssertEqual(WordsStore.position(day: day), 0)
    }
}
