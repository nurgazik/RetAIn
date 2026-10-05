import XCTest
@testable import RetAIn

/// The two exercises are independent (D57): each has its own next word and progress.
final class PracticeStepTests: XCTestCase {
    private func item(_ id: Int, fill: Bool = true, filled: Bool = false, written: Bool = false,
                      status: String = "learning") -> PracticeItem {
        let a = PracticeItem.Attempt(correct: 1, verdict: "natural", reason: nil, fix: nil, answer: "x")
        return PracticeItem(wordId: id, word: "w\(id)", definition: "d", box: 0,
                            fill: fill ? .init(text: "A _____ b.", source: "model", answer: nil) : nil,
                            attempts: .init(fill: filled ? a : nil, write: written ? a : nil), status: status)
    }

    func testEachExerciseWalksItsOwnWords() {
        let items = [item(1, filled: true), item(2, written: true)]
        XCTAssertEqual(PracticeExercise.fill.next(items), 1)
        XCTAssertEqual(PracticeExercise.write.next(items), 0)
    }

    func testWritingNeedsNoFillInFirst() {
        XCTAssertEqual(PracticeExercise.write.next([item(1), item(2)]), 0)
    }

    func testAWordWithoutAFillInIsOnlyInWriting() {
        let items = [item(1, fill: false)]
        XCTAssertNil(PracticeExercise.fill.next(items))
        XCTAssertEqual(PracticeExercise.fill.progress(items).total, 0)
        XCTAssertEqual(PracticeExercise.write.next(items), 0)
    }

    func testRetainedWordsLeaveBothExercises() {
        let items = [item(1, status: "retained"), item(2, filled: true, written: true)]
        XCTAssertNil(PracticeExercise.fill.next(items)); XCTAssertNil(PracticeExercise.write.next(items))
    }

    func testProgressIsPerExercise() {
        let items = [item(1, filled: true), item(2, fill: false), item(3, written: true)]
        let f = PracticeExercise.fill.progress(items), w = PracticeExercise.write.progress(items)
        XCTAssertEqual(f.done, 1); XCTAssertEqual(f.total, 2)
        XCTAssertEqual(w.done, 1); XCTAssertEqual(w.total, 3)
    }

    func testDecodesTheServerShape() throws {
        let json = #"{"day":"2026-10-04","items":[{"word_id":3,"word":"acumen","definition":"d","box":0,"#
            + #""fill":{"text":"It takes _____.","source":"read"},"attempts":{},"status":"learning"}]}"#
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        let s = try d.decode(PracticeSet.self, from: Data(json.utf8))
        XCTAssertEqual(s.items.first?.fill?.source, "read"); XCTAssertNil(s.items.first?.attempts.fill)
    }
}
