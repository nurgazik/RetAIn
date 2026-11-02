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

    // D66: one list — due and not-yet-due words walk together; words not yet in a round count as left.
    func testOneListWalksInOrder() {
        let items = [item(1, filled: true), item(2, part: "ahead"), item(3)]
        XCTAssertEqual(PracticeExercise.fill.next(items), 1)
        let p = PracticeExercise.fill.progress(items, remaining: 7)
        XCTAssertEqual(p.done, 1); XCTAssertEqual(p.total, 10)
    }

    func testTheListIsDoneOnlyWhenEveryWordIsPractisedAndNoneAreLeft() {
        var set = PracticeSet(day: "2026-10-28", items: [item(1, filled: true), item(2, written: true), item(3, status: "retained"),
                                                       item(4, part: "ahead")], remaining: ["today": 0, "ahead": 12])
        XCTAssertFalse(set.isDone)  // not-yet-due words are still on the list: no gate, no "done for today"
        XCTAssertEqual(set.wordProgress.done, 3); XCTAssertEqual(set.wordProgress.total, 16)
        set.items[3].attempts.write = set.items[1].attempts.write; set.remaining = ["today": 0, "ahead": 0]
        XCTAssertTrue(set.isDone)
    }

    func testAWordWithoutAFillInIsListed() {
        let set = PracticeSet(day: "2026-10-31", items: [item(1, fill: false), item(2, fill: false, written: true), item(3)])
        XCTAssertEqual(set.withoutFill.map(\.wordId), [1])  // once written, it's practised: no longer listed
    }

    func testDecodesRemainingAndPart() throws {
        let json = #"{"day":"2026-10-28","items":[{"word_id":3,"word":"acumen","definition":"d","box":0,"part":"ahead","#
            + #""fill":null,"attempts":{},"status":"learning"}],"remaining":{"today":0,"ahead":40}}"#
        let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase
        let s = try d.decode(PracticeSet.self, from: Data(json.utf8))
        XCTAssertEqual(s.items.first?.part, "ahead"); XCTAssertEqual(s.left, 40)
    }

    /// D72: inside a round each exercise has its own fixed order; rounds still go in list order.
    func testEachExerciseShufflesItsRoundOnItsOwn() {
        let round1 = (1...5).map { item($0) }, round2 = (6...10).map { item($0) }
        let items = round1 + round2
        func walk(_ e: PracticeExercise) -> [Int] {  // answer words in the order the exercise offers them
            var xs = items, out: [Int] = []
            while let i = e.next(xs, day: "2026-11-02") {
                out.append(xs[i].wordId)
                let a = PracticeItem.Attempt(correct: 1, verdict: "natural", reason: nil, fix: nil, answer: "x")
                switch e { case .fill: xs[i].attempts.fill = a; case .write: xs[i].attempts.write = a; case .hangman: xs[i].attempts.hangman = a }
            }
            return out
        }
        let fill = walk(.fill), hang = walk(.hangman)
        XCTAssertEqual(Set(fill.prefix(5)), Set(1...5)); XCTAssertEqual(Set(fill.suffix(5)), Set(6...10))  // rounds in order
        XCTAssertEqual(Set(hang.prefix(5)), Set(1...5))
        XCTAssertNotEqual(fill, hang, "two exercises walk the same order")
        XCTAssertNotEqual(fill, Array(1...10), "no shuffle at all")
        XCTAssertEqual(walk(.fill), fill, "the order changes on reopening")
        XCTAssertNotEqual(PracticeExercise.fill.next(items, day: "2026-11-03"), nil)
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
        XCTAssertNil(s.items.first?.part); XCTAssertEqual(s.left, 0)  // a set from before D60
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
