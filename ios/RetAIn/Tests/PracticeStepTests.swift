import XCTest
@testable import RetAIn

/// The two exercises are independent (D57): each has its own next word and progress.
final class PracticeStepTests: XCTestCase {
    private func item(_ id: Int, fill: Bool = true, filled: Bool = false, written: Bool = false,
                      status: String = "learning", part: String? = nil) -> PracticeItem {
        let a = PracticeItem.Attempt(correct: 1, verdict: "natural", reason: nil, fix: nil, answer: "x")
        return PracticeItem(wordId: id, word: "w\(id)", definition: "d", box: 0,
                            fill: fill ? .init(text: "A _____ b.", source: "model", answer: nil) : nil,
                            attempts: .init(fill: filled ? a : nil, write: written ? a : nil), status: status, part: part)
    }

    // D60: today's set and review ahead walk separately; words not yet in a round count as left.
    func testPartsWalkSeparately() {
        let items = [item(1, part: "ahead"), item(2), item(3, filled: true)]
        XCTAssertEqual(PracticeExercise.fill.next(items, in: "today"), 1)
        XCTAssertEqual(PracticeExercise.fill.next(items, in: "ahead"), 0)
        let p = PracticeExercise.fill.progress(items, in: "today", remaining: 7)
        XCTAssertEqual(p.done, 1); XCTAssertEqual(p.total, 9)
    }

    func testTodaysSetIsDoneWhenEveryWordIsPractisedAndNoneAreLeft() {
        var set = PracticeSet(day: "2026-10-28", items: [item(1, filled: true), item(2, written: true), item(3, status: "retained"),
                                                       item(4, part: "ahead")], remaining: ["today": 0, "ahead": 12])
        XCTAssertTrue(set.isDone("today"))
        XCTAssertEqual(set.wordProgress("ahead").done, 0); XCTAssertEqual(set.wordProgress("ahead").total, 13)
        set.remaining?["today"] = 2
        XCTAssertFalse(set.isDone("today"))
        XCTAssertEqual(set.wordProgress("today").total, 5)
    }

    func testDecodesRemainingAndPart() throws {
        let json = #"{"day":"2026-10-28","items":[{"word_id":3,"word":"acumen","definition":"d","box":0,"part":"ahead","#
            + #""fill":null,"attempts":{},"status":"learning"}],"remaining":{"today":0,"ahead":40}}"#
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        let s = try d.decode(PracticeSet.self, from: Data(json.utf8))
        XCTAssertEqual(s.items.first?.section, "ahead"); XCTAssertEqual(s.left("ahead"), 40)
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
        XCTAssertNil(s.items.first?.fill?.hint)
        XCTAssertEqual(s.items.first?.section, "today"); XCTAssertEqual(s.left("today"), 0)  // a set from before D60
    }

    func testDecodesWrongTriesAndAWrongResult() throws {
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        let fill = #"{"text":"It takes _____.","source":"model","wrong":[{"answer":"album","meaning":"A book of photos."}]}"#
        XCTAssertEqual(try d.decode(PracticeItem.Fill.self, from: Data(fill.utf8)).wrong?.first?.answer, "album")
        let r = try d.decode(FillResult.self, from: Data(#"{"correct":false,"answer":"album","meaning":null}"#.utf8))
        XCTAssertFalse(r.correct); XCTAssertNil(r.expected)
    }

    func testDecodesAHintAlreadyAskedFor() throws {
        let json = #"{"text":"It takes _____.","source":"model","hint":["acumen","album","cumin","acorn"]}"#
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        XCTAssertEqual(try d.decode(PracticeItem.Fill.self, from: Data(json.utf8)).hint?.count, 4)
    }
}
