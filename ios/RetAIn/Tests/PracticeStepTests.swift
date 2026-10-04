import XCTest
@testable import RetAIn

/// The practice order (D56): every fill-in first, then every sentence, then the summary.
final class PracticeStepTests: XCTestCase {
    private func item(_ id: Int, fill: Bool = true, filled: Bool = false, written: Bool = false,
                      status: String = "learning") -> PracticeItem {
        let a = PracticeItem.Attempt(correct: 1, verdict: "natural", reason: nil, fix: nil, answer: "x")
        return PracticeItem(wordId: id, word: "w\(id)", definition: "d", box: 0,
                            fill: fill ? .init(text: "A _____ b.", source: "model", answer: nil) : nil,
                            attempts: .init(fill: filled ? a : nil, write: written ? a : nil), status: status)
    }

    func testFillInsComeBeforeAnyWriting() {
        XCTAssertEqual(PracticeStep.next([item(1), item(2)]), .fill(0))
        XCTAssertEqual(PracticeStep.next([item(1, filled: true), item(2)]), .fill(1))
        XCTAssertEqual(PracticeStep.next([item(1, filled: true), item(2, filled: true)]), .write(0))
    }

    func testAWordWithoutAFillInGoesStraightToWriting() {
        XCTAssertEqual(PracticeStep.next([item(1, fill: false)]), .write(0))
    }

    func testSummaryWhenAllDoneOrRetained() {
        XCTAssertEqual(PracticeStep.next([item(1, filled: true, written: true), item(2, status: "retained")]), .summary)
    }

    func testProgressCountsTwoExercisesPerWordWithAFillIn() {
        let p = PracticeStep.progress([item(1, filled: true), item(2, fill: false)])
        XCTAssertEqual(p.done, 1); XCTAssertEqual(p.total, 3)
    }

    func testDecodesTheServerShape() throws {
        let json = #"{"day":"2026-10-04","items":[{"word_id":3,"word":"acumen","definition":"d","box":0,"#
            + #""fill":{"text":"It takes _____.","source":"read"},"attempts":{},"status":"learning"}]}"#
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        let s = try d.decode(PracticeSet.self, from: Data(json.utf8))
        XCTAssertEqual(s.items.first?.fill?.source, "read"); XCTAssertNil(s.items.first?.attempts.fill)
    }
}
